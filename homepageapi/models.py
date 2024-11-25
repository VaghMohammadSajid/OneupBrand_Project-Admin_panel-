from django.db import models
from apps.catalogue.models import Product
from django.contrib.auth.models import User
from oscar.core.loading import get_model
Basket = get_model("basket", "Basket")



class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    is_wishlist = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s wishlist item for {self.product.title}"


class CreditAmountUser(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    cart = models.ForeignKey(Basket,on_delete=models.CASCADE)
    amount = models.IntegerField()