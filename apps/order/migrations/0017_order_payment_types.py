# Generated by Django 4.2.6 on 2024-02-26 00:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0016_remove_order_payment_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_types",
            field=models.CharField(
                blank=True,
                choices=[
                    ("razorpay", "razorpay"),
                    ("cash_on_delivery", "cash_on_delivery"),
                ],
                default="cash_on_delivery",
                max_length=100,
                null=True,
            ),
        ),
    ]
