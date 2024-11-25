# Generated by Django 4.2.6 on 2023-12-23 07:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0026_predefined_product_options"),
        ("homepageapi", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiProductAttributeValue",
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
                    "product_attribute_value",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="catalogue.productattributevalue",
                    ),
                ),
            ],
        ),
    ]
