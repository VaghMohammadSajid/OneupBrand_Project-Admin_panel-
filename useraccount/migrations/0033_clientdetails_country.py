# Generated by Django 4.2.6 on 2024-05-31 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("useraccount", "0032_clientdetails_designation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientdetails",
            name="country",
            field=models.CharField(default="", max_length=50),
            preserve_default=False,
        ),
    ]