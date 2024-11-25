# Generated by Django 4.2.6 on 2024-06-07 12:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0025_alter_order_payment_types"),
        ("wallet", "0002_wallethistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="wallethistory",
            name="order",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="order.order",
            ),
        ),
    ]