from rest_framework import serializers
from oscar.core.loading import get_model
from oscarapi.utils.loading import get_api_classes

VoucherSerializer, OfferDiscountSerializer = get_api_classes(
    "serializers.basket", ["VoucherSerializer", "OfferDiscountSerializer"]
)
from django.contrib.auth import get_user_model

User = get_user_model()
from decimal import Decimal
from oscarapi.utils.settings import overridable

Basket = get_model("basket", "Basket")
Category = get_model("catalogue", "Category")
Voucher = get_model("voucher", "Voucher")
from oscarapi.serializers.fields import (
    DrillDownHyperlinkedRelatedField,
    TaxIncludedDecimalField,
)
from oscarapi.serializers.utils import (
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
)
from oscarapi import settings

# class CategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ('id', 'numchild', 'name', 'description', 'image', 'slug')


class OfferDiscountSerializer(
    serializers.Serializer
):  # pylint: disable=abstract-method
    description = serializers.CharField()
    name = serializers.CharField()
    amount = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="discount"
    )


class VoucherDiscountSerializer(OfferDiscountSerializer):
    voucher = VoucherSerializer(required=False)


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    lines = serializers.HyperlinkedIdentityField(view_name="basket-lines-list")
    offer_discounts = OfferDiscountSerializer(many=True, required=False)
    total_excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False
    )
    total_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False
    )
    total_incl_tax = TaxIncludedDecimalField(
        excl_tax_field="total_excl_tax", decimal_places=2, max_digits=12, required=False
    )
    total_incl_tax_excl_discounts = TaxIncludedDecimalField(
        excl_tax_field="total_excl_tax_excl_discounts",
        decimal_places=2,
        max_digits=12,
        required=False,
    )
    total_tax = TaxIncludedDecimalField(
        excl_tax_value=Decimal("0.00"), decimal_places=2, max_digits=12, required=False
    )
    currency = serializers.CharField(required=False)
    voucher_discounts = VoucherDiscountSerializer(many=True, required=False)
    owner = serializers.HyperlinkedRelatedField(
        view_name="user-detail",
        required=False,
        allow_null=True,
        queryset=User.objects.all(),
    )

    class Meta:
        model = Basket
        fields = overridable(
            "OSCARAPI_BASKET_FIELDS",
            default=(
                "id",
                "owner",
                "status",
                "lines",
                "url",
                "total_excl_tax",
                "total_excl_tax_excl_discounts",
                "total_incl_tax",
                "total_incl_tax_excl_discounts",
                "total_tax",
                "currency",
                "voucher_discounts",
                "offer_discounts",
                "is_tax_known",
            ),
        )


class UpdateQuantitySerializer(serializers.Serializer):
    quantity = serializers.IntegerField()
    product_id = serializers.IntegerField()


class VoucherSerializer(OscarModelSerializer):
    class Meta:
        model = Voucher
        fields = settings.VOUCHER_FIELDS


# Address API
# from oscar.apps.address.models import UserAddress

UserAddress = get_model("address", "UserAddress")


class UserAddressSerializer(serializers.ModelSerializer):
    country_printable_name = serializers.CharField(
        source="country.printable_name", read_only=True
    )

    class Meta:
        model = UserAddress
        fields = "__all__"


# wishlist API
from apps.wishlists.models import WishList, Line


class LineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Line
        fields = "__all__"


class WishListSerializer(serializers.ModelSerializer):
    lines = LineSerializer(many=True, read_only=True)

    class Meta:
        model = WishList
        fields = "__all__"
        read_only_fields = ("owner",)


from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")


class CustomProductSerializer(serializers.ModelSerializer):
    is_wishlist = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_is_wishlist(self, obj):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None

        if user and user.is_authenticated:

            return obj.id in user.wishlist.product_ids()
        return False


from mycustomapi.serializers.product import ProductSerializer


class ProductWithStockSerializer(ProductSerializer):
    stock = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = overridable(
            "OSCARAPI_PRODUCTDETAIL_FIELDS",
            default=(
                "url",
                "upc",
                "id",
                "title",
                "description",
                "structure",
                "date_created",
                "date_updated",
                "recommended_products",
                "attributes",
                "categories",
                "product_class",
                "images",
                "price",
                "availability",
                # "is_stockrecords",
                "options",
                "children",
                "is_stockrecords",
                "is_num_allocated",
                "stock",
                # "is_all_child",
                # "is_wishlist",
            ),
        )

    def get_stock(self, obj):

        return ProductStockRecordSerializer(obj.stockrecords.all().first()).data


class AddProductWishlistSerializer(serializers.Serializer):

    url = serializers.HyperlinkedRelatedField(
        view_name="product-detail", queryset=Product.objects, required=True
    )


WishListLine = get_model("wishlists", "Line")


class WishListDetailsSerializer(serializers.ModelSerializer):
    product = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="product-detail"
    )

    class Meta:
        model = WishListLine
        fields = ["id", "wishlist", "product", "quantity", "title"]


from oscar.defaults import *


class PriceSerializer(serializers.Serializer):
    currency = serializers.CharField(
        max_length=12, default=OSCAR_DEFAULT_CURRENCY, required=False
    )
    excl_tax = serializers.DecimalField(decimal_places=2, max_digits=12, required=True)
    incl_tax = TaxIncludedDecimalField(
        excl_tax_field="excl_tax", decimal_places=2, max_digits=12, required=False
    )
    tax = TaxIncludedDecimalField(
        excl_tax_value="0.00", decimal_places=2, max_digits=12, required=False
    )


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


class BestSellerProductSerializer(serializers.ModelSerializer):
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


class FeaturedProductSerializer(serializers.ModelSerializer):
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
            "featured_products",
            "stockrecords",
            "images",
            "attributes",
        ]
