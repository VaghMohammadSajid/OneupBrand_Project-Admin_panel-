# Generated by Django 4.2.10 on 2024-02-29 09:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("MyNewsLetterApi", "0002_alter_templatemodel_message"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscribermodel",
            name="current_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="templatemodel",
            name="current_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]