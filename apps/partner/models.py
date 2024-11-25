from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.apps.partner.abstract_models import AbstractStockRecord, AbstractPartner
from mycustomapi.models import GSTSetup
from decimal import Decimal


class StockRecord(AbstractStockRecord):
    DISCOUNT_TYPE_CHOICES = (
        ("percentage", _("Percentage")),
        ("amount", _("Amount")),
    )

    discount_type = models.CharField(
        _("Discount Type"),
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        blank=True,
        null=True,
    )

    discount = models.DecimalField(
        _("Discount"), decimal_places=2, max_digits=12, blank=True, null=True
    )

    mrp = models.DecimalField(
        _("MRP"), decimal_places=2, max_digits=12, blank=True, null=True
    )

    price = models.DecimalField(
        _("Price"), decimal_places=2, max_digits=12, blank=True, null=True
    )

    gst_rate = models.ForeignKey(
        GSTSetup, on_delete=models.SET_NULL, null=True, blank=True
    )

    base_price = models.DecimalField(
        _("BasePrice"), decimal_places=2, max_digits=12, blank=True, null=True
    )
    gst_value = models.DecimalField(
        _("GstValue"), decimal_places=2, max_digits=12, blank=True, null=True
    )
    breadth = models.DecimalField(
        _("Breadth"), decimal_places=2, max_digits=12, default=1
    )
    height = models.DecimalField(
        _("height"), decimal_places=2, max_digits=12, default=1
    )
    weight = models.DecimalField(
        _("weight"), decimal_places=2, max_digits=12, default=1
    )
    length = models.DecimalField(
        _("Length"), decimal_places=2, max_digits=12, default=1
    )

    def calculate_final_price(self):
        """
        Calculate the final price after applying the discount.
        """
        if self.mrp is not None and self.discount is not None:
            if self.discount_type == "percentage":
                discounted_price = self.mrp * self.discount / 100
                final_price = max(0, round(self.mrp - discounted_price, 2))
                self.price = final_price
            elif self.discount_type == "amount":
                final_price = max(0, round(self.mrp - self.discount, 2))

                self.price = final_price

            return self.price
        return None

    def get_base_price(self):
        if self.price is not None:
            product_price = self.price
            try:
                gst_rate = self.gst_rate.gst_rate.rate
            except:
                gst_rate = 0.0

            base_price = float(product_price) / (1 + float(gst_rate) / 100)

            return base_price

    def calculate_gst_value(self):
        gst_value = float(self.price) - float(self.base_price)
        return gst_value

    def calculate_decimal_gst_value(self):
        return round(Decimal(self.calculate_gst_value()), 2)

        # dynData['base_price'] = round(base_price,2)

    def calculate_discount(self):
        total_difference = self.mrp - self.price
        if total_difference > 0:
            self.discount_type = "amount"
            self.discount = total_difference
        else:
            self.discount = 0

    def save(self, *args, **kwargs):
        if self.price is None:
            self.calculate_final_price()

        self.base_price = self.get_base_price()

        self.gst_value = self.calculate_gst_value()

        self.calculate_discount()

        super().save(*args, **kwargs)

    class Meta:
        app_label = "partner"
        verbose_name = _("Stock record")
        verbose_name_plural = _("Stock records")


class Partner(AbstractPartner):
    warehouse_pin = models.CharField(max_length=15, default="110043")


from django.db.models.signals import post_save
from django.dispatch import receiver
from oscar.apps.partner.models import *
