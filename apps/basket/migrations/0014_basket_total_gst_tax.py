# Generated by Django 4.2.6 on 2024-02-04 05:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("basket", "0013_line_prodcut_gst_tax"),
    ]

    operations = [
        migrations.AddField(
            model_name="basket",
            name="total_gst_tax",
            field=models.FloatField(default=0),
        ),
    ]