import apps.catalogue.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0031_product_featured_products"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productimage",
            name="original",
            field=models.ImageField(
                max_length=255,
                upload_to=apps.catalogue.models.get_image_upload_path,
                verbose_name="Original",
            ),
        ),
    ]
