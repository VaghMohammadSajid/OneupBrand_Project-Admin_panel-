# Generated by Django 4.2.6 on 2023-12-23 08:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("homepageapi", "0002_apiproductattributevalue"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ApiProductAttributeValue",
        ),
    ]