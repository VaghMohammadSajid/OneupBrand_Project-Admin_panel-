# Generated by Django 4.2.6 on 2024-04-01 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mycustomapi", "0003_alter_gstsetup_created_by_alter_gstsetup_updated_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gstsetup",
            name="hsn_code",
            field=models.IntegerField(),
        ),
    ]