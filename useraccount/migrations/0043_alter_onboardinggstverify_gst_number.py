# Generated by Django 4.2.6 on 2024-07-15 04:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("useraccount", "0042_remove_clientdetails_alter_designation_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="onboardinggstverify",
            name="gst_number",
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]