# Generated by Django 4.2.6 on 2024-09-14 10:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("basket", "0016_shippincharge_courier_id"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("homepageapi", "0005_delete_bannermanagement"),
    ]

    operations = [
        migrations.CreateModel(
            name="CreditAmountUser",
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
                ("amount", models.IntegerField()),
                (
                    "cart",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="basket.basket"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
