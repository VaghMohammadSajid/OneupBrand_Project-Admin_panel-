# Generated by Django 4.2.6 on 2024-05-16 10:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0031_product_featured_products"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("bannermanagement", "0017_alter_recordcreatedby_created_by"),
    ]

    operations = [
        migrations.CreateModel(
            name="VoucherRequestUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("voucher_type", models.CharField(max_length=255)),
                (
                    "amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True
                    ),
                ),
                ("no_of_vouchers", models.IntegerField(blank=True, null=True)),
                ("submission_date", models.DateTimeField(auto_now_add=True)),
                (
                    "select_categories",
                    models.ManyToManyField(
                        blank=True, null=True, to="catalogue.category"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
