# Generated by Django 4.2.6 on 2024-05-29 16:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0024_remove_statusreprotordererptoadmin_status_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="payment_types",
            field=models.CharField(
                blank=True,
                choices=[
                    ("razorpay", "razorpay"),
                    ("cash_on_delivery", "cash_on_delivery"),
                    ("Custome", "Custome"),
                    ("Wallet", "Wallet"),
                ],
                default="cash_on_delivery",
                max_length=100,
                null=True,
            ),
        ),
    ]
