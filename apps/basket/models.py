from oscar.apps.basket.abstract_models import (
    AbstractBasket,
    AbstractLine,
    AbstractLineAttribute,
)
from oscar.core.utils import get_default_currency, round_half_up
from django.db import models


class Basket(AbstractBasket):
    total_gst_tax = models.FloatField(default=0)


class Line(AbstractLine):
    prodcut_gst_tax = models.FloatField(default=0)


class LineAttribute(AbstractLineAttribute):
    pass


class ShippinCharge(models.Model):
    charge = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE)
    courier_id = models.CharField(max_length=30, blank=True, null=True)
