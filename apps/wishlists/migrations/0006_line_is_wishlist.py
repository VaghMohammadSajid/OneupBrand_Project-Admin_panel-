# Generated by Django 3.2.23 on 2024-01-25 18:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wishlists", "0005_auto_20240125_2044"),
    ]

    operations = [
        migrations.AddField(
            model_name="line",
            name="is_wishlist",
            field=models.BooleanField(default=False),
        ),
    ]