# Generated by Django 4.2.6 on 2024-05-24 15:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wallet", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="WalletHistory",
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
                ("wallet_used_amount", models.IntegerField()),
                ("wallet_used_time", models.DateTimeField(auto_now=True)),
                (
                    "wallet",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="history",
                        to="wallet.wallet",
                    ),
                ),
            ],
        ),
    ]
