from django.db import models
from django.dispatch import receiver

from apps.catalogue.models import Category
from useraccount.models import ClientDetails
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save, post_save, post_delete
import logging
logger = logging.getLogger(__name__)


class Bannermanagement(models.Model):
    image = models.ImageField(upload_to="banners/")
    title = models.CharField(max_length=255, blank=True, null=True)
    link = models.CharField(max_length=255, blank=True, null=True)

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, blank=True, null=True
    )
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    active = models.BooleanField(default=True)
    current_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Banner-{self.pk} -  "


class CategoryPromotionSet(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    current_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name


class CategoryPromotion(models.Model):
    image = models.ImageField(upload_to="CategoryPromotion/")
    title = models.CharField(max_length=255, blank=True, null=True)
    set_name = models.ForeignKey(
        CategoryPromotionSet, on_delete=models.CASCADE, default=1
    )
    Link = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, blank=True, null=True
    )
    current_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return (
            f"Banner-{self.pk} - {self.title} - Set: {self.set_name.name} - {self.Link}"
        )


from oscar.core.loading import get_model

ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class Brand(models.Model):
    brand_name = models.CharField(max_length=80, null=True, blank=True)
    logo = models.ImageField(upload_to="brand_logos/", null=True, blank=True)
    current_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.brand_name}"


from django.contrib.auth.models import User
from decimal import Decimal
from oscar.apps.offer.models import ConditionalOffer

from oscar.core.loading import get_model
from django.apps import apps
from oscar.apps.voucher.models import VoucherSet as vo


class VoucherSet(models.Model):
    voucher = models.OneToOneField(vo, on_delete=models.CASCADE, null=True, blank=True)
    vouchername = models.CharField(max_length=255, default="default_value")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voucher_type = models.CharField(max_length=255)

    createDate = models.DateTimeField(auto_now_add=True)
    is_ship_charge = models.BooleanField(default=False)
    shipping_charges = models.IntegerField()
    clubable = models.BooleanField(default=True)
    club_number = models.CharField(default=1)
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="created_voucher_sets",
    )
    is_shipping_included = models.BooleanField(default=False)
    voucher_amount = models.DecimalField(max_digits=15,decimal_places=3,blank=True,null=True)
    PERCENTAGE, FIXED, MULTIBUY, FIXED_PRICE = (
        "Percentage",
        "Absolute",
        "Multibuy",
        "Fixed price",
    )
    SHIPPING_PERCENTAGE, SHIPPING_ABSOLUTE, SHIPPING_FIXED_PRICE = (
        "Shipping percentage",
        "Shipping absolute",
        "Shipping fixed price",
    )
    TYPE_CHOICES = (
        (PERCENTAGE, _("Discount is a percentage off of the product's value")),
        (FIXED, _("Discount is a fixed amount off of the product's value")),
        (MULTIBUY, _("Discount is to give the cheapest product for free")),
        (FIXED_PRICE, _("Get the products that meet the condition for a fixed price")),
        (SHIPPING_ABSOLUTE, _("Discount is a fixed amount of the shipping cost")),
        (SHIPPING_FIXED_PRICE, _("Get shipping for a fixed price")),
        (
            SHIPPING_PERCENTAGE,
            _("Discount is a percentage off of the shipping cost"),
        ),
    )
    amount_type = models.CharField(max_length=128, choices=TYPE_CHOICES, blank=True,null=True)

    def __str__(self):
        return f"{self.vouchername} - {self.voucher_type}"

    def save(self, *args, **kwargs):
        if not self.voucher:
            ob = vo.objects.get(name=self.vouchername)
            self.voucher = ob
            super().save(*args, **kwargs)


@receiver(post_delete, sender=VoucherSet)
def delete_voucher_when_voucherset_deleted(sender, instance, **kwargs):
    try:
        if instance.voucher:
            instance.voucher.delete()
    except:
        logger.error("error in deleting voucher while deleting user",exc_info=True)

class RecordCreatedBy(models.Model):
    conditionoffer = models.OneToOneField(
        ConditionalOffer,
        on_delete=models.CASCADE,
        related_name="created_users",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        User,
        related_name="created_users_record",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


class VoucherRequestUser(models.Model):
    VOUCHER_CHOICE = [("Requested", "Requested"), ("Created", "Created"), ("Closed", "Closed")]
    uuid = models.CharField(unique=True, blank=True, null=True)

    # voucher_request_name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    select_categories = models.ManyToManyField(Category)
    # voucher_type = models.CharField(max_length=255)
    amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    no_of_vouchers = models.IntegerField(null=True, blank=True)
    # club_type = models.CharField(max_length=255,null=True, blank=True)# this field is store a ex: clubable or not
    # gst_type = models.CharField(max_length=255,null=True, blank=True)# this field is store a ex: gst included...
    # type_of_price = models.CharField(max_length=255,null=True,blank=True)
    # shipping_type = models.CharField(max_length=255,null=True, blank=True)# this field is store a ex: shipping included...
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=VOUCHER_CHOICE, default="Requested")

    def __str__(self):
        return f"{self.uuid} - {self.user} - {self.status}"


from django.utils import timezone


def update_uuid_on_save(sender, instance, created, **kwargs):
    if created:
        current_year = timezone.now().year

        # Find the latest voucher count for the current year
        last_voucher_count = VoucherRequestUser.objects.filter(
            submission_date__year=current_year
        ).count()

        # Increment the count by 1 for the new instance
        instance.uuid = f"{current_year}{instance.pk}{last_voucher_count + 1}"
        instance.save(update_fields=["uuid"])


# Connect signal handler to post_save signal
from django.db.models.signals import post_save

post_save.connect(update_uuid_on_save, sender=VoucherRequestUser)


class FixedVoucherCondition(models.Model):
    max_value = models.IntegerField()
    min_value = models.IntegerField()
    voucherset = models.OneToOneField(VoucherSet,on_delete=models.CASCADE,related_name="condition")



