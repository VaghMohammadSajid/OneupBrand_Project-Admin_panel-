from typing import Iterable
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
import logging
from oscar.core.loading import get_model

logger = logging.getLogger(__name__)


Order = get_model("order", "Order")

# Create your models here.


class Wallet(models.Model):
    amount = models.PositiveBigIntegerField(default=0)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.user.username

    def get_amount(self):
        return self.amount

    def remove_amount(self, deduction_amount, order=None):
        logger.debug(deduction_amount)
        try:
            wallet_history = WalletHistory(
                wallet=self, wallet_used_amount=-deduction_amount, order=order
            )
            wallet_history.save()
            return True
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(e)
            return False

    def total_amount_added(self):
        return WalletHistory.objects.filter(
            wallet=self, wallet_used_amount__gte=0
        ).aggregate(total_amount=Sum("wallet_used_amount"))

    def total_amount_radeemed(self):
        return WalletHistory.objects.filter(
            wallet=self, wallet_used_amount__lte=0
        ).aggregate(total_amount=Sum("wallet_used_amount"))

    def remove_none(self, func):
        value = func()
        if value.get("total_amount") == None:
            return 0
        else:
            return value.get("total_amount")

    def recalculate(self):

        self.amount = self.remove_none(self.total_amount_added) + self.remove_none(
            self.total_amount_radeemed
        )
        self.save()
        logger.debug(self.amount)


class WalletHistory(models.Model):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.SET_NULL, related_name="history", null=True
    )
    wallet_used_amount = models.IntegerField()
    wallet_used_time = models.DateTimeField(auto_now=True)
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, blank=True, null=True, related_name="wallet"
    )

    def save(self) -> None:
        try:
            s = super().save()
        except Exception as e:
            pass

        self.wallet.recalculate()
        return s

    def __str__(self) -> str:
        return self.wallet.user.username


def grand_total_added_to_client():
    return WalletHistory.objects.filter(wallet_used_amount__gte=0).aggregate(
        total_amount=Sum("wallet_used_amount")
    )


def grand_total_amount_radeemed_by_cliend():
    return WalletHistory.objects.filter(wallet_used_amount__lte=0).aggregate(
        total_amount=Sum("wallet_used_amount")
    )
