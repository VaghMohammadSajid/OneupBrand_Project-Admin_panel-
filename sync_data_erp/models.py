from django.db import models
from oscar.core.loading import get_model

# Create your models here.

Product = get_model("catalogue", "Product")


class FailedOrder(models.Model):
    order_number = models.CharField(max_length=60)
    order_failed_time = models.DateTimeField(auto_now_add=True)
    order_failed_trace_back = models.TextField()

    def __str__(self) -> str:
        return self.order_number


class StockSyncReport(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    inventory = models.IntegerField(blank=True, null=True)
    last_stock = models.IntegerField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.product.title
