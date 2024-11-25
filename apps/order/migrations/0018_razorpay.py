# Generated by Django 4.2.6 on 2024-02-26 00:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0017_order_payment_types"),
    ]

    operations = [
        migrations.CreateModel(
            name="Razorpay",
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
                ("payment_id", models.CharField(blank=True, max_length=100)),
                ("payment_signature", models.CharField(blank=True, max_length=100)),
                ("total_amount", models.IntegerField()),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("ACCEPTED", "ACCEPTED"),
                            ("FAILED", "FAILED"),
                            ("PENDING", "PENDING"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "order_id",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="order.order",
                    ),
                ),
            ],
        ),
    ]
