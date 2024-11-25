from typing import Iterable
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
import logging
from oscar.core.loading import get_model

logger = logging.getLogger(__name__)

Cart = get_model("basket", "Basket")

Order = get_model("order", "Order")

# Create your models here.


class Credit(models.Model):
    amount = models.PositiveBigIntegerField(default=0)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credit_gst = models.CharField(max_length=100, blank=True, null=True)
    credit_shipping_type = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.user.username

    def get_amount(self):
        return self.amount

    def add_amount(self, add_amount, order=None, credit_req=None):
        logger.debug(add_amount)

        try:
            credit_history = CreditHistory(
                credit=self,
                credit_used_amount=add_amount,
                order=order,
                credit_request=credit_req,
            )
            credit_history.save()
            return True
        except Exception as e:
            logger.error("Error in saing credit", exc_info=True)
            return False

    def remove_amount(self, deduction_amount, order=None):
        logger.debug(deduction_amount)
        if self.get_amount() - deduction_amount < 0:
            return False
        try:
            credit_history = CreditHistory(
                credit=self, credit_used_amount=-deduction_amount, order=order
            )
            credit_history.save()
            return True
        except Exception as e:
            return False

    def total_amount_added(self):
        return CreditHistory.objects.filter(
            credit=self, credit_used_amount__gte=0
        ).aggregate(total_amount=Sum("credit_used_amount"))

    def total_amount_radeemed(self):
        return CreditHistory.objects.filter(
            credit=self, credit_used_amount__lte=0
        ).aggregate(total_amount=Sum("credit_used_amount"))

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


class CreditRequestUser(models.Model):

    credit_request_id = models.CharField(
        unique=True, blank=True, null=True, max_length=50
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Requested")
    reason = models.TextField(blank=True, null=True, default="")
    erp = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.status} - {self.credit_request_id}"


class CreditHistory(models.Model):
    credit = models.ForeignKey(
        Credit, on_delete=models.SET_NULL, related_name="history", null=True
    )
    credit_used_amount = models.IntegerField()
    credit_used_time = models.DateTimeField(auto_now=True)
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, blank=True, null=True, related_name="Credit"
    )
    credit_request = models.OneToOneField(
        CreditRequestUser, on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self) -> None:
        try:
            s = super().save()
        except Exception as e:
            pass

        self.credit.recalculate()
        return s

    # def __str__(self) -> str:
    #     return self.credit.user.username


def grand_total_added_to_client():
    return CreditHistory.objects.filter(credit_used_amount__gte=0).aggregate(
        total_amount=Sum("credit_used_amount")
    )


def grand_total_amount_radeemed_by_cliend():
    return CreditHistory.objects.filter(credit_used_amount__lte=0).aggregate(
        total_amount=Sum("credit_used_amount")
    )


from django.utils import timezone


def update_credit_request_id_on_save(sender, instance, created, **kwargs):
    if created:
        current_year = timezone.now().year

        # Find the latest voucher count for the current year
        last_credit_count = CreditRequestUser.objects.filter(
            submission_date__year=current_year
        ).count()

        # Increment the count by 1 for the new instance
        instance.credit_request_id = (
            f"{current_year}{instance.pk}{last_credit_count + 1}"
        )
        instance.save(update_fields=["credit_request_id"])


# Connect the signal handler to the post_save signal
from django.db.models.signals import post_save

post_save.connect(update_credit_request_id_on_save, sender=CreditRequestUser)


class OtpForCredit(models.Model):
    otp = models.CharField(max_length=6)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
