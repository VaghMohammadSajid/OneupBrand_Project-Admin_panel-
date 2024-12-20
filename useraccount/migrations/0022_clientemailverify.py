# Generated by Django 4.2.6 on 2024-05-22 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("useraccount", "0021_delete_intermediateproducttableparent"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClientEmailVerify",
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
                ("email", models.EmailField(max_length=254)),
                ("otp", models.IntegerField(default=0)),
            ],
        ),
    ]
