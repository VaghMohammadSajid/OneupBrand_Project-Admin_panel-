# Generated by Django 4.2.6 on 2024-05-03 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bannermanagement", "0011_alter_voucherset_shipping_charges"),
    ]

    operations = [
        migrations.AddField(
            model_name="voucherset",
            name="is_ship_charge",
            field=models.BooleanField(default=False),
        ),
    ]
