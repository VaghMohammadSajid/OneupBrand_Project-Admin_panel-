# Generated by Django 4.2.6 on 2024-01-12 17:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("address", "0007_city_states_postalcode_city_state"),
    ]

    operations = [
        migrations.RenameField(
            model_name="postalcode",
            old_name="state",
            new_name="city",
        ),
    ]
