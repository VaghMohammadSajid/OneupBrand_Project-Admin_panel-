from collections.abc import Iterable
from django.db import models

from django.contrib.auth.models import User


# code
from django.db.models.signals import post_save, pre_delete

from django.dispatch import receiver


# Create your models here.


class ApiKey(models.Model):
    key = models.CharField(max_length=255, unique=True)

    class Meta:
        app_label = "mycustomapi"


# models for tax in oneup
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="created_user",
    )
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Last Updated Date")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="updated_user",
    )

    class Meta:
        abstract = True


class GSTGroup(BaseModel):
    gst_group_code = models.CharField(max_length=100)
    description = models.TextField()
    rate = models.FloatField(default=0.0)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="code_created_user",
    )
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Last Updated Date")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="code_updated_user",
    )


GST_RATE_SLAB = (
    ("single", "Single"),
    ("multiple", "Multiple"),
)


class GSTSetup(BaseModel):
    hsn_code = models.IntegerField()
    hsn_description = models.TextField()
    gst_rate = models.ForeignKey(
        GSTGroup, on_delete=models.CASCADE, null=True, blank=True
    )
    sgst_rate = models.FloatField(default=0.0)  # 50% of gst rate
    cgst_rate = models.FloatField(default=0.0)  # 50% of gst rate
    igst_rate = models.FloatField(default=0.0)  # 100 % of gst rate
    # gst_rate_slab = models.CharField(max_length=20, choices=GST_RATE_SLAB, blank=True, null=True)
    # base_rate_from = models.FloatField(default  = 0.0)
    # base_rate_to = models.FloatField(default  = 0.0)

    create_date = models.DateTimeField(auto_now_add=True, verbose_name="Creation Date")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="created_user",
    )
    updated_date = models.DateTimeField(auto_now=True, verbose_name="Last Updated Date")
    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="updated_user",
    )

    class Meta:
        ordering = ["-create_date"]

    def save(self, *args, **kwargs):
        # Check if the gst_rate field is not None
        if self.gst_rate is not None:
            # Update sgst_rate, cgst_rate, and igst_rate based on gst_rate
            gst_rate_value = self.gst_rate.rate
            self.sgst_rate = 0.5 * gst_rate_value
            self.cgst_rate = 0.5 * gst_rate_value
            self.igst_rate = gst_rate_value

        super(GSTSetup, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.gst_rate.gst_group_code
