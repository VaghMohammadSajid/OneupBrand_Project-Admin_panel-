# Generated by Django 4.2.6 on 2024-03-28 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0030_product_specifications"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="featured_products",
            field=models.BooleanField(default=False),
        ),
    ]
