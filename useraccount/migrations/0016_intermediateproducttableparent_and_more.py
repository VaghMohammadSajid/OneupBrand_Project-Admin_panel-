# Generated by Django 4.2.6 on 2024-05-09 16:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("useraccount", "0015_uploadproductjson"),
    ]

    operations = [
        migrations.CreateModel(
            name="IntermediateProductTableParent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("upc", models.CharField(max_length=50)),
                ("title", models.CharField(max_length=50)),
                ("hsn_code", models.CharField(max_length=50)),
                ("description", models.CharField(max_length=50)),
                ("Specification", models.CharField(max_length=50)),
                ("image", models.TextField()),
                ("product_type", models.CharField(max_length=50)),
                ("is_public", models.CharField(max_length=50)),
                ("is_discountable", models.CharField(max_length=50)),
                ("best_seller", models.CharField(max_length=50)),
                ("standard_rate", models.CharField(max_length=50)),
                ("num_in_stock", models.CharField(max_length=50)),
                ("brand", models.CharField(max_length=50)),
                ("first_category", models.TextField(max_length=50)),
                ("structure", models.CharField(max_length=50)),
                ("attributes", models.TextField()),
                ("recommended_products", models.TextField()),
                (
                    "json_relation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="useraccount.uploadproductjson",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="IntermediateProductTableChild",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("upc", models.CharField(max_length=100)),
                ("title", models.CharField(max_length=100)),
                ("description", models.CharField(max_length=50)),
                ("Specification", models.CharField(max_length=50)),
                ("image", models.TextField()),
                ("product_type", models.CharField(max_length=100)),
                ("is_public", models.CharField(max_length=100)),
                ("is_discountable", models.CharField(max_length=100)),
                ("best_seller", models.CharField(max_length=100)),
                ("standard_rate", models.CharField(max_length=100)),
                ("num_in_stock", models.CharField(max_length=100)),
                ("brand", models.CharField(max_length=100)),
                ("first_category", models.CharField(max_length=100)),
                ("attributes", models.TextField()),
                ("Parent_UPC", models.CharField(max_length=100)),
                ("structure", models.CharField(max_length=100)),
                ("recommended_products", models.TextField()),
                ("shipment_dimensions", models.TextField()),
                ("length", models.IntegerField()),
                ("width", models.IntegerField()),
                ("height", models.IntegerField()),
                ("weight", models.IntegerField()),
                ("supplier", models.CharField(max_length=100)),
                ("low_stock_threshold", models.CharField(max_length=100)),
                ("mrp", models.IntegerField()),
                ("discount", models.IntegerField()),
                ("price", models.IntegerField()),
                ("gst_rate", models.CharField()),
                (
                    "json_relation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="useraccount.uploadproductjson",
                    ),
                ),
            ],
        ),
    ]