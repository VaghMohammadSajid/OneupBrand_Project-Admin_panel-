# Generated by Django 4.2.6 on 2024-04-23 14:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("offer", "0011_rangeproductfileupload_included"),
        ("DiscountManagement", "0003_alter_proxyclassforrange_attr_delete_attrname"),
    ]

    operations = [
        migrations.RenameField(
            model_name="proxyclassforrange",
            old_name="all_product",
            new_name="_all_product",
        ),
        migrations.AddField(
            model_name="proxyclassforrange",
            name="range",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="offer.range",
            ),
        ),
    ]
