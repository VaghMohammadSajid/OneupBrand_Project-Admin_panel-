# Generated by Django 4.2.6 on 2024-05-24 15:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("useraccount", "0024_intermediateproducttablechild_created_status"),
    ]

    operations = [
        migrations.RenameField(
            model_name="intermediateproducttablechild",
            old_name="created_status",
            new_name="product_status",
        ),
    ]
