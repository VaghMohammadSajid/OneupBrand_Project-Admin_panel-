# Generated by Django 4.2.6 on 2024-03-15 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("partner", "0013_stockrecord_gst_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="stockrecord",
            name="breadth",
            field=models.DecimalField(
                decimal_places=2, default=1, max_digits=12, verbose_name="Breadth"
            ),
        ),
        migrations.AddField(
            model_name="stockrecord",
            name="height",
            field=models.DecimalField(
                decimal_places=2, default=1, max_digits=12, verbose_name="height"
            ),
        ),
        migrations.AddField(
            model_name="stockrecord",
            name="length",
            field=models.DecimalField(
                decimal_places=2, default=1, max_digits=12, verbose_name="Length"
            ),
        ),
        migrations.AddField(
            model_name="stockrecord",
            name="weight",
            field=models.DecimalField(
                decimal_places=2, default=1, max_digits=12, verbose_name="weight"
            ),
        ),
    ]
