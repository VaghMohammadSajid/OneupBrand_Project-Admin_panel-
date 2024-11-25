# Generated by Django 4.2.6 on 2024-05-13 06:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("bannermanagement", "0016_recordcreatedby_conditionoffer_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="recordcreatedby",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="created_users_record",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]