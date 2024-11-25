# from oscar.apps.address.models import *
from oscar.apps.address.abstract_models import (
    AbstractShippingAddress,
    AbstractUserAddress,
    AbstractBillingAddress,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


class Choices(models.TextChoices):
    HOME = "HOME", "HOME"
    OFFICE = "OFFICE", "OFFICE"
    OTHER = "OTHER", "OTHER"


class UserAddress(AbstractUserAddress):
    address_type = models.CharField(
        max_length=100,
        choices=Choices.choices,
        default=Choices.HOME,
        blank=True,
        null=True,
    )

    email = models.EmailField(
        verbose_name="Email", max_length=255, blank=True, null=True
    )


class ShippingAddress(AbstractShippingAddress):
    email = models.EmailField(
        verbose_name="Email", max_length=255, blank=True, null=True
    )
    address_type = models.CharField(
        max_length=100,
        choices=Choices.choices,
        default=Choices.HOME,
        blank=True,
        null=True,
    )


class States(models.Model):
    state_name = models.CharField(max_length=100)
    country = models.ForeignKey(
        "address.Country",
        on_delete=models.CASCADE,
        verbose_name=_("Country"),
        related_name="state_country",
    )


class City(models.Model):
    city_name = models.CharField(max_length=100)
    state = models.ForeignKey(
        States, on_delete=models.CASCADE, verbose_name=_("States")
    )


class PostalCode(models.Model):
    postal_code = models.CharField(max_length=20)
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name=_("City"))


class BillingAddress(AbstractBillingAddress):
    phone_number = PhoneNumberField(
        _("Phone number"),
        blank=True,
        help_text=_("In case we need to call you about your order"),
    )
    email = models.EmailField(
        verbose_name="Email", max_length=255, blank=True, null=True
    )


from oscar.apps.address.models import Country
