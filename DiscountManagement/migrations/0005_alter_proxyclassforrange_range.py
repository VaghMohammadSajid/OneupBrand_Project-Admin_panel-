# Generated by Django 4.2.6 on 2024-04-23 18:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("offer", "0011_rangeproductfileupload_included"),
        (
            "DiscountManagement",
            "0004_rename_all_product_proxyclassforrange__all_product_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="proxyclassforrange",
            name="range",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="back_range",
                to="offer.range",
            ),
        ),
    ]
