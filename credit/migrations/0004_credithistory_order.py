# Generated by Django 4.2.6 on 2024-07-03 11:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0027_shippingaddress_address_type"),
        ("credit", "0003_remove_credithistory_cart_credit_credit_gst_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="credithistory",
            name="order",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="Credit",
                to="order.order",
            ),
        ),
    ]
