# Generated by Django 4.2.6 on 2023-11-02 07:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("useraccount", "0006_alter_clientdetails_user"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="clientdetails",
            name="aadhar_no",
        ),
    ]
