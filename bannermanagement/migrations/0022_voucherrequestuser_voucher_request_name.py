# Generated by Django 4.2.6 on 2024-05-22 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bannermanagement", "0021_merge_20240521_1433"),
    ]

    operations = [
        migrations.AddField(
            model_name="voucherrequestuser",
            name="voucher_request_name",
            field=models.CharField(default="default_name", max_length=255),
            preserve_default=False,
        ),
    ]
