# Generated by Django 4.2.6 on 2024-05-02 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bannermanagement", "0004_voucherset_shipping_charges"),
    ]

    operations = [
        migrations.AlterField(
            model_name="voucherset",
            name="shipping_charges",
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]
