# Generated by Django 4.2.6 on 2024-07-05 07:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("useraccount", "0037_productuploaderrorlog_productuploadsucceslog_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="uniquestrings",
            name="client",
        ),
        migrations.AddField(
            model_name="uniquestrings",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
