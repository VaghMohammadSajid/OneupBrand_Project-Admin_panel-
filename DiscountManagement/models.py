from django.db import models

# Create your models here.

from django.db import models
from django.utils.translation import gettext_lazy as _
import logging

# Create your models here.
logger = logging.getLogger(__name__)

from oscar.apps.offer.models import ConditionalOffer

ConditionalOffer.TYPE_CHOICES = (
    # (ConditionalOffer.SITE, _("Site offer - available to all users")),
    (
        ConditionalOffer.VOUCHER,
        ("Voucher - only available after entering " "the appropriate voucher code"),
    ),
    (ConditionalOffer.USER, _("User offer - available to certain types of user")),
    (
        ConditionalOffer.SESSION,
        _(
            "Session offer - temporary offer, available for "
            "a user for the duration of their session"
        ),
    ),
)

from django.db import models
from oscar.core.loading import get_model
from itertools import chain
from django.contrib.auth.models import User

Product = get_model("catalogue", "Product")
AttributeOption = get_model("catalogue", "AttributeOption")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
Range = get_model("offer", "Range")
ProductCategory = get_model("catalogue", "ProductCategory")
Category = get_model("catalogue", "Category")


class ProxyClassForRange(models.Model):
    included_categories = models.ManyToManyField(
        Category, related_name="proxy_included_categories"
    )
    _all_product = models.ManyToManyField(Product, related_name="all_product")
    attr = models.ManyToManyField(AttributeOption)
    range = models.OneToOneField(
        Range,
        on_delete=models.CASCADE,
        related_name="back_range",
        null=True,
        blank=True,
    )

    def contains_product(self, product):
        return self._all_product.filter(id=product.id).exists()

    def save(self, *args, **kwargs):
        try:
            self.product_query_set()
        except Exception as e:
            pass
        super(ProxyClassForRange, self).save(*args, **kwargs)

    def product_query_set(self):
        if self.included_categories.all().count() <= 0:
            all_attr = self.attr.all()
            logger.debug(f"{all_attr=}")
            value_option = ProductAttributeValue.objects.filter(
                value_option__in=all_attr
            )
            logger.debug(f"{value_option=}")
            product_list = [
                single_value_option.product
                for single_value_option in value_option
                if single_value_option.product.structure == "child"
            ]
            logger.debug(f"{product_list=}")
            self._all_product.clear()
            self._all_product.add(*product_list)
            return self._all_product
        else:
            all_category_with_child = [
                single_category.get_descendants_and_self()
                for single_category in self.included_categories.all()
            ]
            flattened_list = list(chain.from_iterable(all_category_with_child))
            logger.debug(f"{flattened_list}")
            logger.debug(f"{all_category_with_child=}")
            all_product_category = ProductCategory.objects.filter(
                category__in=flattened_list
            )

            logger.debug(
                f"{all_product_category=} \n {self.included_categories.all()=}"
            )
            all_product_object = [
                single_product_cate.product.children.all()
                for single_product_cate in all_product_category
            ]
            flattened_list_of_all_product = list(
                chain.from_iterable(all_product_object)
            )
            logger.debug(f"{all_product_object=}")
            logger.debug(f"{flattened_list_of_all_product}")
            self._all_product.clear()
            self._all_product.add(*flattened_list_of_all_product)
            return self._all_product

    def all_product(self):
        return self.product_query_set()


Order = get_model("order", "order")
Product = get_model("catalogue", "Product")
Stock = get_model("partner", "StockRecord")


class VoucherAllocationBYLine(models.Model):
    STATUS_CHOICES = (
        ("Inclusive", "Inclusive"),
        ("Exclusive", "Exclusive"),
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="voucher_allocation_by_line"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    MRP = models.IntegerField()
    listing_price = models.IntegerField()
    voucher_value = models.FloatField()
    unit_price = models.FloatField()
    taxable_amount = models.FloatField()
    gst_value = models.FloatField()
    order_value = models.FloatField()
    quantity = models.IntegerField(null=True, blank=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, null=True, blank=True)
    shipping = models.IntegerField(blank=True, null=True)
    tax_type = models.CharField(
        blank=True, null=True, choices=STATUS_CHOICES, default="Inclusive"
    )

    def save(self, *args, **kwargs):
        if self.tax_type == "Inclusive":
            self.taxable_amount = float(self.unit_price) / (
                1 + float(self.stock.gst_rate.gst_rate.rate) / 100
            )
            self.gst_value = self.unit_price - self.taxable_amount
            self.order_value = (self.gst_value + self.taxable_amount) * self.quantity
        else:
            self.gst_value = (
                float(self.stock.gst_rate.gst_rate.rate) / 100
            ) * self.unit_price
            self.taxable_amount = self.unit_price
            self.order_value = (self.gst_value + self.taxable_amount) * self.quantity

        super().save(*args, **kwargs)

    def __str__(self):
        return self.order.number


Basket = get_model("basket", "basket")


class GiftCartTotalAMount(models.Model):
    cart = models.ForeignKey(Basket, on_delete=models.CASCADE)
    total_amount = models.FloatField()

    def __str__(self):
        return f"{self.cart}"
