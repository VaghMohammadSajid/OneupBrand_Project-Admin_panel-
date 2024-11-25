# Generated by Django 4.2.6 on 2023-11-02 07:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("useraccount", "0005_clientdetails_delete_userdetails"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clientdetails",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]