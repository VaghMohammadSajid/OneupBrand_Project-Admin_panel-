# Generated by Django 4.2.6 on 2024-03-09 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("address", "0008_rename_state_postalcode_city"),
    ]

    operations = [
        migrations.AddField(
            model_name="useraddress",
            name="email",
            field=models.EmailField(
                blank=True, max_length=255, null=True, verbose_name="Email"
            ),
        ),
    ]
