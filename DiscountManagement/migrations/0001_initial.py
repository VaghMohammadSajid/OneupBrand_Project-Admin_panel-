# Generated by Django 4.2.6 on 2024-04-22 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalogue", "0031_product_featured_products"),
    ]

    operations = [
        migrations.CreateModel(
            name="AttrName",
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
                ("attr_name", models.CharField(max_length=100)),
                ("attr_value", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="ProxyClassForRange",
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
                (
                    "all_product",
                    models.ManyToManyField(
                        related_name="all_product", to="catalogue.product"
                    ),
                ),
                ("attr", models.ManyToManyField(to="DiscountManagement.attrname")),
                (
                    "included_categories",
                    models.ManyToManyField(
                        related_name="proxy_included_categories", to="catalogue.product"
                    ),
                ),
            ],
        ),
    ]