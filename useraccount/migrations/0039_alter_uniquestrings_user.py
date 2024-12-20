# Generated by Django 4.2.6 on 2024-07-05 07:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("useraccount", "0038_remove_uniquestrings_client_uniquestrings_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="uniquestrings",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="use",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
