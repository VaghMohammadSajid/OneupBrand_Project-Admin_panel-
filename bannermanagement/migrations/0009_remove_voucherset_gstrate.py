# Generated by Django 4.2.6 on 2024-05-02 17:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bannermanagement", "0008_alter_voucherset_shipping_charges"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="voucherset",
            name="gstrate",
        ),
    ]