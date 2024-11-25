from rest_framework import serializers
from .models import Bannermanagement, VoucherRequestUser

from apps.catalogue.models import Category


class BannermanagementSerializer(serializers.ModelSerializer):
    category_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Bannermanagement
        fields = [
            "id",
            "image",
            "title",
            "category",
            "category_id",
            "category_name",
            "active",
            "logo",
            "link",
        ]

    def get_category_id(self, obj):
        return obj.category.id if obj.category else None

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "meta_title",
            "meta_description",
            "image",
            "slug",
            "is_public",
            "ancestors_are_public",
            "full_name",
            "full_slug",
        ]


from apps.catalogue.models import Product
from apps.catalogue.models import ProductImage


from rest_framework import serializers

from rest_framework import serializers


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("original",)


class ProductSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    primary_image_url = serializers.SerializerMethodField()
    root_category = serializers.SerializerMethodField()  # Add this line

    class Meta:
        model = Product
        fields = "__all__"

    def get_categories(self, product):
        return [category.name for category in product.get_categories()]

    def get_root_category(self, product):  # Add this method
        return product.categories.first().get_root().name

    def get_primary_image_url(self, product):
        primary_image = product.images.filter(display_order=0).first()
        if primary_image:
            return primary_image.original.url
        return None


from rest_framework import serializers
from .models import CategoryPromotion


class CategoryPromotionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = CategoryPromotion
        fields = ("id", "image", "title", "category", "category_name", "Link")


# newarivels

from oscar.core.loading import get_model
from mycustomapi.serializers.product import ProductImageSerializer

Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")
ProductImage = get_model("catalogue", "ProductImage")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class ProductStockRecordSerializer(serializers.ModelSerializer):
    discount_type = serializers.CharField()
    discount = serializers.CharField()
    mrp = serializers.CharField()
    price = serializers.CharField()
    num_in_stock = serializers.CharField()

    class Meta:
        model = StockRecord
        fields = ("discount_type", "discount", "mrp", "price", "num_in_stock")


class LatestProductSerializer(serializers.ModelSerializer):
    stockrecords = ProductStockRecordSerializer(many=True)
    images = ProductImageSerializer(many=True, required=False)
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "structure",
            "title",
            "description",
            "best_seller",
            "stockrecords",
            "images",
            "attributes",
        ]

    def get_attributes(self, obj):
        attributes = {}
        attribute_values = ProductAttributeValue.objects.filter(product=obj)
        for attribute_value in attribute_values:
            attributes[attribute_value.attribute.name] = (
                attribute_value.value.option if attribute_value.value else None
            )
        return attributes


from DiscountManagement.serializer import CategorySerilaizer


class VoucherRequestUserSerializer(serializers.ModelSerializer):
    select_categories = CategorySerilaizer(many=True, read_only=True)

    class Meta:
        model = VoucherRequestUser
        fields = [
            "user",
            "select_categories",
            # "voucher_type",
            "amount",
            "no_of_vouchers",
            "status",
            "submission_date",
            "uuid",
            # "shipping_type",
            # "type_of_price",
            # "gst_type",
            # "club_type",

        ]
