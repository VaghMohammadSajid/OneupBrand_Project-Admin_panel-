# Generated by Django 4.2.6 on 2024-05-23 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0022_order_erp_status"),
    ]

    operations = [
        migrations.CreateModel(
            name="StatusReprotOrderErpToAdmin",
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
                ("order_id", models.CharField(max_length=25)),
                ("status", models.CharField(max_length=100)),
                ("new_status_time", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
