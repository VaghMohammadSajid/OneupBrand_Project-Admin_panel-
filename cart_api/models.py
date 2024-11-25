from django.db import models
from oscar.core.loading import get_model

StockRecord = get_model("partner", "StockRecord")
Cart = get_model("basket", "Basket")


# Create your models here.


class Freeze(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    stock = models.ForeignKey(StockRecord, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.quantity}"
