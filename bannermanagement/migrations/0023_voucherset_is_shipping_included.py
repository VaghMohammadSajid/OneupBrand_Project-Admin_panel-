# Generated by Django 4.2.6 on 2024-06-26 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bannermanagement", "0022_voucherrequestuser_voucher_request_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="voucherset",
            name="is_shipping_included",
            field=models.BooleanField(default=False),
        ),
    ]
