# Generated by Django 4.2.1 on 2024-01-15 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("homepageapi", "0003_delete_apiproductattributevalue"),
    ]

    operations = [
        migrations.CreateModel(
            name="Bannermanagement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("image", models.ImageField(upload_to="banners/")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
            ],
        ),
    ]
