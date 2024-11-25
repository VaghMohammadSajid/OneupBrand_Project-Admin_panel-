# Generated by Django 4.2.6 on 2024-05-23 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0023_statusreprotordererptoadmin"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="statusreprotordererptoadmin",
            name="status",
        ),
        migrations.AddField(
            model_name="statusreprotordererptoadmin",
            name="awb_no",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="statusreprotordererptoadmin",
            name="new_status",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="statusreprotordererptoadmin",
            name="old_status",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="statusreprotordererptoadmin",
            name="order_id",
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
    ]
