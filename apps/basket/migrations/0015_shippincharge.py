# Generated by Django 4.2.6 on 2024-03-21 06:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("basket", "0014_basket_total_gst_tax"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShippinCharge",
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
                (
                    "charge",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=12, null=True
                    ),
                ),
                (
                    "basket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="basket.basket"
                    ),
                ),
            ],
        ),
    ]