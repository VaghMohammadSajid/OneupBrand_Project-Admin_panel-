# pylint: disable=unbalanced-tuple-unpacking
from rest_framework import generics
from rest_framework.response import Response

from oscar.core.loading import get_class, get_model
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from mycustomapi.utils.categories import find_from_full_slug
from mycustomapi.utils.loading import get_api_classes, get_api_class

Selector = get_class("partner.strategy", "Selector")
(
    CategorySerializer,
    ProductLinkSerializer,
    ProductSerializer,
    ProductStockRecordSerializer,
    AvailabilitySerializer,
) = get_api_classes(
    "serializers.product",
    [
        "CategorySerializer",
        "ProductLinkSerializer",
        "ProductSerializer",
        "ProductStockRecordSerializer",
        "AvailabilitySerializer",
    ],
)

PriceSerializer = get_api_class("serializers.checkout", "PriceSerializer")


__all__ = ("ProductList", "ProductDetail", "ProductPrice", "ProductAvailability")

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
StockRecord = get_model("partner", "StockRecord")


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductLinkSerializer

    def get_queryset(self):
        """
        Allow filtering on structure so standalone and parent products can
        be selected separately, eg::

            http://127.0.0.1:8000/api/products/?structure=standalone

        or::

            http://127.0.0.1:8000/api/products/?structure=parent
        """
        qs = super(ProductList, self).get_queryset()
        structure = self.request.query_params.get("structure")
        if structure is not None:
            return qs.filter(structure=structure)

        return qs


# class ProductDetail(generics.RetrieveAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer
#     # permission_classes = (IsOwner,)
from apps.catalogue.models import ProductImage
from apps.catalogue.models import ProductAttributeValue

WishListLine = get_model("wishlists", "Line")
from rest_framework.generics import ListAPIView


@permission_classes([IsAuthenticated])
class ProductDetail(ListAPIView):

    def list(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")

        queryset = Product.objects.filter(id=pk).first()
        serializer = ProductSerializer(queryset, context={"request": request})
        require_data = serializer.data

        try:
            require_data["description"] = queryset.parent.description
            require_data["paren_category"] = queryset.parent.product_class.name
            print(queryset.parent.product_class.name)
            # import pdb;pdb.set_trace()
            require_data["paren_category_id"] = queryset.parent.product_class.id
        except:
            require_data["description"] = ""
            require_data["paren_category"] = ""
            require_data["paren_category_id"] = ""

        for fields in queryset._meta.fields:
            print(fields, getattr(queryset, fields.name))

        print(queryset.parent.product_class, "aaaaaaaaaaa")

        obj = StockRecord.objects.filter(
            product__id=pk
        ).first()  # Use first() instead of values() if expecting a single object

        if obj:
            require_data["mrp"] = obj.mrp
            require_data["discount_type"] = obj.discount_type
            require_data["discount"] = obj.discount

        else:
            # Handle the case when there is no matching object
            require_data["mrp"] = None
            require_data["discount_type"] = None
            require_data["discount"] = None

        if WishListLine.objects.filter(
            wishlist__owner__id=request.user.id, product__id=pk
        ).exists():

            require_data["is_wishlist"] = True
        else:
            require_data["is_wishlist"] = False

        all_product = Product.objects.filter(id=pk).values("parent")
        parent_id = all_product[0]["parent"]

        if parent_id != None:
            obj = Product.objects.filter(parent=parent_id)
            all_pro = Product.objects.filter(parent=parent_id).values(
                "id",
                "title",
                "parent",
                "parent__title",
                "structure",
                "description",
                "specifications",
                "upc",
                "is_discountable",
                "rating",
                "slug",
                "description",
                "meta_title",
                "meta_description",
                "is_discountable",
                "attributes",
                "product_class",
                "parent__categories__name",
                "parent__categories__id",
            )
            arrayProd = []
            for data in all_pro:
                dynData = data
                jjj = data["id"]
                objec = ProductImage.objects.filter(product=jjj).values(
                    "original", "display_order"
                )
                dynData["image"] = objec
                product_objec = Product.objects.get(id=dynData["id"])
                dynData["parent__categories__name"] = product_objec.parent.categories.all()[0].name
                dynData["parent__categories__id"] = product_objec.parent.categories.all()[0].id
                attributes = ProductAttributeValue.objects.filter(product=jjj).values(
                    "attribute__name",
                    "value_text",
                    "value_integer",
                    "value_multi_option__option",
                    "value_boolean",
                    "value_float",
                    "value_richtext",
                    "value_option__option",
                )
                dynData["attributes"] = attributes
                is_wishlist = WishListLine.objects.filter(
                    wishlist__owner__id=request.user.id, product__id=jjj
                ).values("is_wishlist")
                dynData["is_wishlist"] = is_wishlist
                stock_record = StockRecord.objects.filter(product=jjj).values(
                    "mrp",
                    "discount",
                    "discount_type",
                    "price",
                    "gst_rate__igst_rate",
                    "base_price",
                    "num_in_stock",
                    "num_allocated",
                )
                dynData["stock_record"] = stock_record.first()
                arrayProd.append(dynData)

            array = []
            count = 0
            for i in obj:

                strategy = Selector().strategy()
                info = strategy.fetch_for_product(i)
                objprice = info.price.excl_tax

                array.append(objprice)
                arrayProd[count]["price"] = objprice
                count = count + 1
                array = []
            require_data["arrayProd"] = arrayProd

            return Response(require_data)
        else:
            return Response(require_data)


class ProductPrice(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = PriceSerializer

    def get(
        self, request, pk=None, *args, **kwargs
    ):  # pylint: disable=redefined-builtin,arguments-differ
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = PriceSerializer(
            strategy.fetch_for_product(product).price, context={"request": request}
        )
        return Response(ser.data)


class ProductStockRecords(generics.ListAPIView):
    serializer_class = ProductStockRecordSerializer
    queryset = StockRecord.objects.all()

    def get_queryset(self):
        product_pk = self.kwargs.get("pk")
        return super().get_queryset().filter(product_id=product_pk)


class ProductStockRecordDetail(generics.RetrieveAPIView):
    serializer_class = ProductStockRecordSerializer
    queryset = StockRecord.objects.all()


class ProductAvailability(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = AvailabilitySerializer

    def get(
        self, request, pk=None, *args, **kwargs
    ):  # pylint: disable=redefined-builtin,arguments-differ
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = AvailabilitySerializer(
            strategy.fetch_for_product(product).availability,
            context={"request": request},
        )
        return Response(ser.data)


class CategoryList(generics.ListAPIView):
    queryset = Category.get_root_nodes()
    serializer_class = CategorySerializer

    def get_queryset(self):
        breadcrumb_path = self.kwargs.get("breadcrumbs", None)
        if breadcrumb_path is None:
            return super(CategoryList, self).get_queryset()

        return find_from_full_slug(breadcrumb_path, separator="/").get_children()


class CategoryDetail(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
