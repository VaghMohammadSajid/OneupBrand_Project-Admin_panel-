# Generated by Django 4.2.6 on 2024-05-09 06:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("bannermanagement", "0013_voucherset_club_number_voucherset_clubable"),
    ]

    operations = [
        migrations.AddField(
            model_name="voucherset",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="created_voucher_sets",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
