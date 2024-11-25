# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-13 08:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0004_auto_20160111_1108"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="guest_email",
            field=models.EmailField(
                blank=True, max_length=254, verbose_name="Guest email address"
            ),
        ),
    ]
