# Generated by Django 4.2.6 on 2024-07-01 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bannermanagement", "0023_voucherset_is_shipping_included"),
    ]

    operations = [
        migrations.AddField(
            model_name="voucherrequestuser",
            name="uuid",
            field=models.CharField(blank=True, null=True, unique=True),
        ),
    ]
