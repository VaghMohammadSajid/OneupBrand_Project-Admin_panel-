# Generated by Django 4.2.6 on 2024-08-09 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("useraccount", "0052_alter_onboardinggstverify_gst_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="onboardinggstverify",
            name="gst_number",
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
