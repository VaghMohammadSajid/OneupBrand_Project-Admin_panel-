from django.db import models
from oscar.apps.catalogue.abstract_models import (
    AbstractProduct,
    AbstractOption,
    AbstractAttributeOptionGroup,
    AbstractAttributeOption,
    AbstractProductClass,
    AbstractCategory,
    AbstractProductCategory,
    AbstractProductRecommendation,
    AbstractProductAttribute,
    AbstractProductAttributeValue,
    AbstractProductImage,
)
from oscar.apps.catalogue.managers import ProductQuerySet
import datetime
import posixpath
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


def get_image_upload_path(instance, filename):
    return posixpath.join(
        datetime.datetime.now().strftime(settings.OSCAR_IMAGE_FOLDER), filename
    )


class ProductClass(AbstractProductClass):
    pass


class Category(AbstractCategory):
    # is_first_cat = models.BooleanField(default=False)
    pass


class ProductCategory(AbstractProductCategory):
    pass


class Product(AbstractProduct):
    best_seller = models.BooleanField(default=False)
    specifications = models.TextField(blank=True, null=True)
    featured_products = models.BooleanField(default=False)
    # objects = ProductQuerySet.as_manager()


class ProductRecommendation(AbstractProductRecommendation):
    pass


class ProductAttribute(AbstractProductAttribute):
    pass


class ProductAttributeValue(AbstractProductAttributeValue):
    pass


class AttributeOptionGroup(AbstractAttributeOptionGroup):
    pass


class AttributeOption(AbstractAttributeOption):
    pass


class Option(AbstractOption):
    pass


class ProductImage(AbstractProductImage):
    original = models.ImageField(
        _("Original"), upload_to=get_image_upload_path, max_length=255
    )

    def delete(self, *args, **kwargs):
        # Delete the image file from storage
        self.original.delete()
        # Call the superclass delete method
        super().delete(*args, **kwargs)
