# Generated by Django 2.0.7 on 2018-11-15 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0006_orderstatuschange"),
    ]

    operations = [
        migrations.AlterField(
            model_name="communicationevent",
            name="date_created",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="Date"
            ),
        ),
        migrations.AlterField(
            model_name="orderstatuschange",
            name="date_created",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="Date Created"
            ),
        ),
        migrations.AlterField(
            model_name="paymentevent",
            name="date_created",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="Date created"
            ),
        ),
        migrations.AlterField(
            model_name="shippingevent",
            name="date_created",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, verbose_name="Date Created"
            ),
        ),
    ]
