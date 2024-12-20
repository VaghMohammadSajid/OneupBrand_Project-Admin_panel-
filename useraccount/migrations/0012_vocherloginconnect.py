# Generated by Django 4.2.6 on 2024-04-02 11:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("voucher", "0011_alter_voucher_id_alter_voucherapplication_id_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("useraccount", "0011_voucheruser"),
    ]

    operations = [
        migrations.CreateModel(
            name="VocherLoginConnect",
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
                ("count", models.IntegerField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "voucher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="voucher.voucher",
                    ),
                ),
            ],
        ),
    ]
