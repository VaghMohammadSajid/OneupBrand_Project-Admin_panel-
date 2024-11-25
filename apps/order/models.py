from oscar.apps.order.abstract_models import AbstractOrder
from django.db import models


class Order(AbstractOrder):
    class Choices(models.TextChoices):
        RAZORPAY = "razorpay", "razorpay"
        CASH_ON_DELIVERY = "cash_on_delivery", "cash_on_delivery"
        CUSTOME = "Custome", "Custome"
        Wallet = "Wallet", "Wallet"

    payment_types = models.CharField(
        max_length=100,
        choices=Choices.choices,
        default=Choices.CASH_ON_DELIVERY,
        blank=True,
        null=True,
    )
    erp_status = models.CharField(max_length=100, null=True, blank=True)


stat = (("ACCEPTED", "ACCEPTED"), ("FAILED", "FAILED"), ("PENDING", "PENDING"))
raz_status = (('created','created'),('authorized','authorized'),('captured','captured'),('failed','failed'),('NOT_CHECKED','NOT_CHECKED'))

class Razorpay(models.Model):
    payment_id = models.CharField(max_length=100, blank=True)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.IntegerField()
    status = models.CharField(choices=stat, max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    raz_status = models.CharField(choices=raz_status,default='NOT_CHECKED')


    def __str__(self) -> str:
        return f"{self.order_id}"


class Fship_order_details(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    sales_order_id = models.CharField(max_length=60)
    awb_no = models.CharField(max_length=40)
    api_order_id = models.CharField(max_length=40)
    pick_up_id = models.CharField(max_length=40)
    fship_pick_up_id = models.CharField(max_length=40)


class StatusReprotOrderErpToAdmin(models.Model):
    order_id = models.CharField(max_length=25, blank=True, null=True)
    new_status = models.CharField(max_length=100, blank=True, null=True)
    old_status = models.CharField(max_length=100, blank=True, null=True)
    awb_no = models.CharField(max_length=200, blank=True, null=True)
    new_status_time = models.DateTimeField(auto_now_add=True)


from oscar.apps.order.models import *


class OrderJson(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_json = models.JSONField()

    def __str__(self):
        return self.order.number
