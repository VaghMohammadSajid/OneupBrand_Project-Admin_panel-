from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.catalogue.models import Category

from decimal import Decimal

from .pagination import CustomLimitOffsetPagination

# Create your views here.
from oscarapi.permissions import IsOwner
from rest_framework import generics
from apps.catalogue.models import Category
from apps.catalogue.models import Product
from apps.catalogue.models import ProductAttributeValue

from homepageapi.serializers import (
    BasketSerializer,
    UpdateQuantitySerializer,
    VoucherSerializer,
)

# from mycustomapi.basket import operations
from oscarapi.basket import operations
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

# categorie api-----------------------

from oscar.apps.voucher.models import Voucher
from DiscountManagement.models import GiftCartTotalAMount

from homepageapi.models import WishlistItem
from .utils import (
    create_voucher_data,
    check_voucher,
    add_voucher_details,
    voucher_calc_in_cart,
    CreateCreditForCart
)


# from homepageapi.serializers import CategorySerializer


# # Category = get_model('catalogue', 'Category')


class CategoryTreeView(APIView):
    def get(self, request, *args, **kwargs):
        # obj=Category.get_children()
        obj = Category.objects.filter(Category.get_children).values("name")
        return Response({"msg": obj})


from apps.wishlists.models import WishList, Line
from oscar.apps.partner.strategy import Selector
from apps.catalogue.models import ProductImage
from apps.partner.models import StockRecord


class CategoryWisedProduct(APIView):

    def get(self, request, id, *args, **kwargs):
        obj = Product.objects.filter(categories=id)
        objconcat = Product.objects.filter(categories=id).values(
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
        )

        arrayProd = []
        for data in objconcat:
            dynData = data
            jjj = data["id"]
            objec = ProductImage.objects.filter(product=jjj).values("original")
            Varient_Price = StockRecord.objects.filter(product__parent__id=jjj).values(
                "price"
            )
            dynData["image"] = objec
            dynData["Varient_Price"] = Varient_Price
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

        return Response({"data": arrayProd})


from oscar.core.loading import get_model

Line = get_model("basket", "Line")


# #user wise get cart api ----------------
# @permission_classes([IsAuthenticated])
# class BasketView(APIView):
#     serializer_class = BasketSerializer
#     permission_classes = (IsOwner,)

#     def get_gst_tax():
#         pass
#     def get(self, request, *args, **kwargs):
#         total_price_exclusive_tax = 0.0
#         total_gst_tax = 0.0
#         basket = operations.get_basket(request)
#         obj =Line.objects.filter(basket__id=basket.id).values('product')
#         ser = self.serializer_class(basket, context={"request": request})
#         cart_data = ser.data
#         basket = operations.get_basket(request)
#         arrayProd = []
#         obj =Line.objects.filter(basket__id=basket.id).values('product','product__title','price_currency','price_excl_tax','price_incl_tax','quantity')
#         for data in obj:

#             dynData = data
#             product_id = data['product']
#             objec = ProductImage.objects.filter(product=product_id).values('original')

#             # add tax related logics.
#             #base_price = StockRecord.objects.filter(product = product_id).first()
#             # dynData['base_price'] = base_price.base_price
#             # dynData['gst_rate'] = base_price.gst_rate.gst_rate.rate
#             # gst_tax_amount =data['price_excl_tax']-dynData['base_price']
#             # gst_tax_amount = gst_tax_amount*data['quantity']
#             # total_price_exclusive_tax = float(total_price_exclusive_tax)+float(dynData['base_price']*data['quantity'])
#             # total_gst_tax = float(total_gst_tax)+float(gst_tax_amount)
#             # dynData['gst_tax_amount'] = gst_tax_amount
#             dynData["image"] = objec
#             arrayProd.append(dynData)
#         # cart_data['gst_tax_amount'] = total_gst_tax
#         # cart_data['total_price_exclusive_tax'] = total_price_exclusive_tax
#         cart_data['product_deatils'] = arrayProd
#         return Response(cart_data)


# user wise get cart api ----------------
import logging

logger = logging.getLogger(__name__)


@permission_classes([IsAuthenticated])
class BasketView(APIView):
    serializer_class = BasketSerializer
    permission_classes = (IsOwner,)

    def get_gst_tax():
        pass

    def get(self, request, *args, **kwargs):

        gift_excl = False

        total_price_exclusive_tax = 0.0
        total_gst_tax = 0.0
        basket = operations.get_basket(request)
        obj = Line.objects.filter(basket__id=basket.id).values("product")
        ser = self.serializer_class(basket, context={"request": request})
        cart_data = ser.data

        basket = operations.get_basket(request)
        print(cart_data["voucher_discounts"], "its a basket")
        print(cart_data["offer_discounts"], "its a basket")
        try:
            (
                voucher_data_list,
                tota_offer_amount_after_voucher_calculation,
                total_payable,
                basic_amount_radeemable,
                total_tax,
                total_discount,
                balance_payable,
                total_shiping_charge,
            ) = create_voucher_data(basket)
        except Exception as e:
            import traceback

            f = traceback.format_exc()
            logger.error(f"error in exclusive cacl{f}")

            basic_amount_radeemable, total_tax, total_discount, balance_payable = (
                0,
                0,
                0,
                0,
            )
            tota_offer_amount_after_voucher_calculation = 0
            total_payable = 0
            total_shiping_charge = 0
            voucher_data_list = str(e)
        arrayProd = []
        obj = Line.objects.filter(basket__id=basket.id).values(
            "product",
            "product__title",
            "price_currency",
            "price_excl_tax",
            "price_incl_tax",
            "quantity",
        )
        total_product_value = 0
        total_tax2 = 0
        basic_amount_radeemable2 = 0
        total_amount_allocation = 0
        for data in obj:

            dynData = data

            product_id = data["product"]
            objec = ProductImage.objects.filter(product=product_id).values("original")

            base_price = StockRecord.objects.filter(product=product_id).first()
            dynData["base_price"] = round(float(base_price.get_base_price()), 2)
            total_price_exclusive_tax = float(total_price_exclusive_tax) + float(
                dynData["base_price"] * data["quantity"]
            )
            dynData["mrp"] = base_price.mrp
            dynData["discount_type"] = base_price.discount_type
            dynData["discount"] = base_price.discount
            dynData["stock"] = base_price.num_in_stock - base_price.num_allocated
            try:
                dynData["gst_rate"] = base_price.gst_rate.gst_rate.rate
            except:
                dynData["gst_rate"] = 0.0

            logger.debug(f"{float(base_price.calculate_gst_value())=}")
            dynData["gst_tax_amount"] = round(
                float(base_price.calculate_gst_value()), 2
            )

            dynData["image"] = objec
            arrayProd.append(dynData)
            try:
                product_price, tax_amount, taxable_amount, amount_allocation_by_line = (
                    voucher_calc_in_cart(
                        cart=basket,
                        basic_amount_radeemable=basic_amount_radeemable,
                        offer_amount=tota_offer_amount_after_voucher_calculation,
                        stock=base_price,
                        quantity=data["quantity"],
                    )
                )
                dynData["amount_allocation_by_line"] = amount_allocation_by_line

                total_amount_allocation = (
                    total_amount_allocation + amount_allocation_by_line
                )

                total_product_value = total_product_value + (
                    product_price * data["quantity"]
                )
                total_tax2 = total_tax2 + (tax_amount * data["quantity"])
                logger.debug(f"logging tax{total_tax2=} {tax_amount}")
                basic_amount_radeemable2 = basic_amount_radeemable2 + (
                    taxable_amount * data["quantity"]
                )

                gift_excl = True
                logger.debug(
                    f"{tax_amount=} {taxable_amount=} {product_price=} {total_product_value=} {total_tax2=} "
                )

            except:
                import traceback

                f = traceback.format_exc()
                logger.error(f"error in exclusive cacl {f=}")

        try:
            if len(voucher_data_list) > 0:
                for i in arrayProd:
                    if i.get("voucher") == None:
                        i["voucher"] = []
                    for j in voucher_data_list:

                        print(i, j)
                        if i["product"] in j["product"]:
                            i["voucher"].append(j["code"])
        except Exception as e:
            pass
        amount = CreateCreditForCart(user=request.user,cart=basket)
        if not amount == None:
            cart_data["credit_amount"] = amount
        cart_data["product_deatils"] = arrayProd
        # cart_data['voucher_data'] = voucher_data
        cart_data["voucher_list"] = voucher_data_list
        cart_data["offer_tootal_amount"] = tota_offer_amount_after_voucher_calculation
        # if float(cart_data["total_excl_tax_excl_discounts"]) - tota_offer_amount_after_voucher_calculation >= 0:
        # cart_data["total_excl_tax_excl_discounts"] = float(
        # cart_data["total_excl_tax_excl_discounts"]) - tota_offer_amount_after_voucher_calculation
        # else:
        # cart_data["total_excl_tax_excl_discounts"] = 0
        # cart_data['total_gst_payable'] = total_payable

        cart_data["basic_amount_radeemable"] = round(basic_amount_radeemable, 0)
        cart_data["total_amount_allocation"] = round(total_amount_allocation, 0)

        cart_data["total_tax"] = round(total_tax, 0)
        cart_data["total_discount"] = round(total_discount, 0)
        cart_data["balance_payable"] = round(balance_payable, 0)
        cart_data["total_shiping_charge"] = (
            round(float(total_shiping_charge), 0)
            if not total_shiping_charge == None
            else None
        )
        if gift_excl == True:
            # cart_data['basic_amount_radeemable'] = round(basic_amount_radeemable2)
            # cart_data['total_tax'] = round(total_tax2)
            cart_data["balance_payable"] = round(total_product_value)
            try:
                gift_obj = GiftCartTotalAMount.objects.get(cart=basket)
                gift_obj.total_amount = cart_data["balance_payable"]
                gift_obj.save()
            except:
                gift_obj = GiftCartTotalAMount.objects.create(
                    cart=basket, total_amount=cart_data["balance_payable"]
                )

            gift_obj.total_amount = cart_data["balance_payable"]
            gift_obj.save()
        check_voucher(basket=basket)

        return Response(cart_data)

    def calculate_voucher_data(self, voucher_discounts):
        voucher_data = []
        shopping_voucher_original_amount_sum = 0
        shopping_voucher_gst_amount_sum = 0
        gift_voucher_original_amount_sum = 0

        for voucher_discount in voucher_discounts:
            voucher_dict = {}
            voucher_name = voucher_discount["voucher"]["name"]
            voucher_name = voucher_name.split(" - ")[0]
            voucher_dict["name"] = voucher_name
            voucher_set = VoucherSet.objects.filter(vouchername=voucher_name).first()
            if voucher_set:
                voucher_value = Decimal(voucher_discount["amount"])
                print(voucher_discount["amount"])
                gstrate = Decimal(voucher_set.gstrate)
                voucher_value_decimal = Decimal(voucher_value)
                voucher_gst_amount = voucher_value_decimal * (gstrate / (100 + gstrate))
                print(f"{voucher_gst_amount=}")
                original_value = voucher_value_decimal - voucher_gst_amount
                voucher_dict["inclusive_gst_amount"] = round(
                    float(voucher_gst_amount), 2
                )
                voucher_dict["original_value"] = round(float(original_value), 2)
                voucher_dict["voucher_gst_amount"] = round(float(voucher_gst_amount), 2)
                voucher_dict["voucher_type"] = voucher_set.voucher_type
                voucher_data.append(voucher_dict)
                if voucher_set.voucher_type == "shopping voucher":
                    shopping_voucher_original_amount_sum += original_value
                    shopping_voucher_gst_amount_sum += voucher_gst_amount
                elif voucher_set.voucher_type == "gift voucher":
                    gift_voucher_original_amount_sum += original_value
        additional_data = {
            "shopping_voucher_original_amount_sum": round(
                float(shopping_voucher_original_amount_sum), 2
            ),
            "shopping_voucher_gst_amount_sum": round(
                float(shopping_voucher_gst_amount_sum), 2
            ),
            "gift_voucher_original_amount_sum": round(
                float(gift_voucher_original_amount_sum), 2
            ),
        }

        return voucher_data, additional_data



# api for delete cart -------------------


class DeleteCartProduct(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, productid, basketid, *args, **kwargs):
        print(basketid, "pranav")
        obj = Line.objects.filter(product=productid, basket=basketid)
        obj.delete()
        return Response({"obj": "data deleted"})


# product detail api -----------

StockRecord = get_model("partner", "StockRecord")


class GetProductDetailIdWise(APIView):
    def get(self, request, id, *args, **kwargs):
        obj = Product.objects.filter(id=id)
        objconcat = Product.objects.filter(id=id).values(
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
        )

        arrayProd = []
        for data in objconcat:
            dynData = data
            jjj = data["id"]
            objec = ProductImage.objects.filter(product=jjj).values("original")
            dynData["image"] = objec
            att_val = ProductAttributeValue.objects.filter(product=jjj).values(
                "attribute__name",
                "value_text",
                "value_integer",
                "value_multi_option__option",
                "value_boolean",
                "value_float",
                "value_richtext",
                "value_option__option",
            )
            dynData["att_val"] = att_val
            user_id = request.user.id if request.user.is_authenticated else None
            is_wishlist = WishlistItem.objects.filter(
                product_id=jjj, user_id=user_id
            ).exists()
            dynData["is_wishlist"] = is_wishlist
            # Fetch StockRecord data for the current product
            stock_record = StockRecord.objects.filter(product=jjj).values(
                "mrp",
                "discount",
                "discount_type",
                "price",
                "gst_rate__igst_rate",
                "base_price",
                "num_in_stock",
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

        return Response({"data": arrayProd})


# update quantity-----------------


@permission_classes([IsAuthenticated])
class UpdateQuantityOfProduct(APIView):

    def validate(
        self, basket, product, quantity, options
    ):  # pylint: disable=unused-argument
        availability = basket.strategy.fetch_for_product(product).availability

        # check if product is available at all
        if not availability.is_available_to_buy:
            return False, availability.message

        current_qty = basket.product_quantity(product)
        desired_qty = quantity

        # check if we can buy this quantity
        allowed, message = availability.is_purchase_permitted(desired_qty)
        if not allowed:
            return False, message

        # check if there is a limit on amount
        allowed, message = basket.is_quantity_allowed(desired_qty)
        if not allowed:
            return False, message
        return True, None

    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)
        serializer = UpdateQuantitySerializer(data=data)
        serializer_class = BasketSerializer

        basket = operations.get_basket(request)
        print("basket id", basket.id)

        if serializer.is_valid():
            quantity = serializer.validated_data["quantity"]
            product_id = serializer.validated_data["product_id"]
            options = serializer.validated_data.get("options", [])
            product = Product.objects.filter(id=product_id).first()

            basket_valid, message = self.validate(basket, product, quantity, options)
            if not basket_valid:
                return Response({"reason": message})
            print(basket.all_lines())
            if Line.objects.filter(basket_id=basket.id, product_id=product_id).exists():
                line_obj = Line.objects.filter(
                    basket_id=basket.id, product_id=product_id
                ).first()
                lineObj = basket.lines.get(id=line_obj.id)
                lineObj.quantity = quantity
                lineObj.save()

            ser = serializer_class(basket, context={"request": request})

            return Response({"message": "updated successfully", "data": ser.data})
        else:
            return Response({"message": "serializer is not valid"})

        # get count of cart -----------


@permission_classes([IsAuthenticated])
class CartCountOfUser(APIView):
    serializer_class = BasketSerializer
    permission_classes = (IsOwner,)

    def get(self, request, *args, **kwargs):
        basket = operations.get_basket(request)
        obj = (
            Line.objects.filter(basket__id=basket.id, basket__owner=self.request.user)
            .values("product")
            .count()
        )
        return Response({"cart_count": obj})


# this api for get voucher api -----
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

Voucher = get_model("voucher", "Voucher")
from django.utils import timezone
from bannermanagement.models import VoucherSet


class GetVouchersView(APIView):
    def get(self, request):
        now = timezone.now()

        # Fetch data from Voucher model
        vouchers = Voucher.objects.all()
        voucher_data = []
        for voucher in vouchers:
            voucher_dict = {}
            voucher_dict["id"] = voucher.id
            voucher_dict["name"] = voucher.name.split(" - ")[
                0
            ]  # Take only the portion before the hyphen
            voucher_dict["code"] = voucher.code
            voucher_dict["start_datetime"] = voucher.start_datetime
            voucher_dict["end_datetime"] = voucher.end_datetime
            voucher_dict["total_discount"] = voucher.total_discount

            # Find the corresponding VoucherSet for the voucher
            voucher_set = VoucherSet.objects.filter(
                vouchername=voucher_dict["name"]
            ).first()
            if voucher_set:
                # Calculate voucher_value
                voucher_value = sum(
                    offer.benefit.value for offer in voucher.offers.all()
                )
                voucher_dict["voucher_value"] = voucher_value

                # Calculate inclusive_gst_amount, original_value, and gst_amount
                gstrate = Decimal(voucher_set.gstrate)
                voucher_value_decimal = Decimal(voucher_value)
                original_value = voucher_value_decimal / (1 + gstrate / Decimal(100))
                gst_amount = voucher_value_decimal - original_value

                # Assign calculated values to the dictionary
                voucher_dict["inclusive_voucher_amount"] = float(voucher_value)
                voucher_dict["original_value"] = float(original_value)
                voucher_dict["gst_amount"] = float(gst_amount)

            voucher_data.append(voucher_dict)

        return Response({"voucher_data": voucher_data})

    # def get(self,request,*args,**kwargs):
    #     obj=Line.objects.filter(basket_id__owner=self.request.user).count()
    #     return Response({"cartcount":obj})


class VoucherList(generics.ListAPIView):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer


# from oscar.apps.address.models import UserAddress

UserAddress = get_model("address", "UserAddress")

from .serializers import (
    AddProductWishlistSerializer,
    PriceSerializer,
    UserAddressSerializer,
    WishListDetailsSerializer,
)
from rest_framework.generics import get_object_or_404
from rest_framework import status


class AddressCreateAPIView(generics.CreateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AddressListAPIView(generics.ListAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            UserAddress._default_manager.filter(user=self.request.user)
            .select_related("country")
            .order_by("id")
        )

    # No need to use the 'fields' argument here
    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)


class AddressUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)

    def get_object(self):
        address_id = self.kwargs.get("pk")
        return get_object_or_404(self.get_queryset(), pk=address_id)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressDeleteAPIView(generics.DestroyAPIView):
    queryset = UserAddress.objects.all()
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        address_id = self.kwargs.get("id")
        return UserAddress.objects.get(id=address_id)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Address deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


from rest_framework import generics
from oscar.apps.customer.wishlists.views import (
    WishListAddProduct,
    WishListCreateView,
    WishListDetailView,
)
from .serializers import WishListSerializer
from oscar.apps.customer.wishlists.views import (
    WishListCreateView as OscarWishListCreateView,
)
from .wish_list_add_product import WishListAddProduct
from .models import WishlistItem
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.http import HttpRequest


class WishListView(generics.ListAPIView):
    serializer_class = WishListSerializer

    def get_queryset(self):
        return self.request.user.wishlists.all()


class WishListCreateView(generics.CreateAPIView):
    serializer_class = WishListSerializer

    def perform_create(self, serializer):
        wishlist = serializer.save(owner=self.request.user)
        product_id = self.request.data.get("product_id")
        if product_id:
            WishListAddProduct().add_product(wishlist.key, product_id)


class WishListRemoveProductAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        wishlist_key = kwargs.get("key")
        product_id = kwargs.get("product_id")
        print(kwargs, "pranav")

        # Call remove_product to remove the product from the wishlist
        result = WishListAddProduct.remove_product(wishlist_key, product_id)

        if result["success"]:
            msg = _("Product was removed from the wishlist successfully.")
            return JsonResponse({"detail": msg}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(
                {"detail": result["message"]}, status=status.HTTP_404_NOT_FOUND
            )


class SearchApiView(APIView):
    pagination_class = CustomLimitOffsetPagination

    def get(
        self,
        request,
        search_words=None,
        *args,
        **kwargs,
    ):
        if search_words:
            return self.get_search_by_words(request, search_words, *args, **kwargs)
        else:
            return self.get_search_api(request, *args, **kwargs)

    def get_search_api(self, request, *args, **kwargs):

        search_query = request.query_params.get("q", "")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")

        obj = Product.objects.filter(title__icontains=search_query)

        arrayProd = []
        for data in obj:
            # Check if the structure is 'parent', and if so, skip this iteration
            if data.structure == "parent":
                continue

            dynData = {
                "id": data.id,
                "title": data.title,
                "description": data.description,
                "upc": data.upc,
                "is_discountable": data.is_discountable,
                "rating": data.rating,
            }

            objec = ProductImage.objects.filter(product=data.id).values(
                "original", "display_order"
            )
            dynData["image"] = objec

            strategy = Selector().strategy()
            info = strategy.fetch_for_product(data)
            objprice = info.price.excl_tax
            dynData["price"] = objprice

            arrayProd.append(dynData)

        if min_price is not None:
            arrayProd = [
                prod for prod in arrayProd if prod["price"] >= float(min_price)
            ]

        if max_price is not None:
            arrayProd = [
                prod for prod in arrayProd if prod["price"] <= float(max_price)
            ]
        logger.debug(arrayProd)
        code_list = request.GET.getlist("code_list", None)
        if not code_list == None:
            try:
                arrayProd = add_voucher_details(
                    array_prod=arrayProd, code_list=code_list
                )
            except:
                pass

        return Response({"data": arrayProd})

    def get_search_by_words(self, request, search_words, *args, **kwargs):
        words = search_words.split(",")  # Split words by comma
        search_criteria = {}  # Dictionary to hold search criteria

        # Determine search criteria based on input
        for word in words:
            # Check if word matches a brand name
            brand = ProductAttribute.objects.filter(
                name="Brand",
                productattributevalue__value_option__option__icontains=word,
            ).first()
            if brand:
                search_criteria["brand"] = word
                continue

            # Check if word matches an attribute value
            attribute_value = ProductAttributeValue.objects.filter(
                value_option__option__icontains=word
            )
            if attribute_value:
                search_criteria["attribute_value"] = word
                continue

            # Check if word matches a category
            category = Category.objects.filter(name__icontains=word)
            if category.exists():
                search_criteria.setdefault("categories", []).append(category)
                continue

            # If not a brand or attribute value, consider it as part of product name
            search_criteria["product_name"] = word

        # Filter products based on search criteria
        products = Product.objects.all()
        if "product_name" in search_criteria:
            products = products.filter(title__icontains=search_criteria["product_name"])
        if "brand" in search_criteria:
            products = products.filter(
                attribute_values__attribute=brand,
                attribute_values__value_option__option__icontains=search_criteria[
                    "brand"
                ],
            )
        if "attribute_value" in search_criteria:
            products = products.filter(
                attribute_values__value_option__option__icontains=search_criteria[
                    "attribute_value"
                ]
            )
        if "categories" in search_criteria:
            category_queries = Q()
            for categories_list in search_criteria["categories"]:
                print("category", categories_list)
                category_query = Q()
                for category in categories_list:
                    print("testing:", category)
                    if category.depth == 1:
                        subcategories = category.get_descendants()
                        if subcategories:
                            print("subcategories:", subcategories)
                            category_query |= Q(parent__categories__in=subcategories)
                        else:
                            category_query |= Q(parent__categories=category)
                    else:
                        category_query |= Q(parent__categories=category)
                        print("category_query:", category_query)
                category_queries |= category_query
            products = products.filter(category_queries)
            print("products:", products)

        arrayProd = []
        all_categories = []
        seen_categories = set()

        for product_data in products:
            # Check if the structure is 'parent', and if so, skip this iteration
            if product_data.structure == "parent" or not product_data.is_public:
                continue

            product = {
                "id": product_data.id,
                "title": product_data.title,
                "structure": product_data.structure,
                "description": product_data.description,
                "date_created": product_data.date_created,
                "stockrecords__price": (
                    product_data.stockrecords.first().price
                    if product_data.stockrecords.first()
                    else None
                ),
            }
            stock_record = StockRecord.objects.filter(product=product_data.id).values(
                "mrp", "discount", "discount_type", "num_in_stock"
            )
            print(stock_record)
            product["stock_record"] = stock_record.first()
            product_images = ProductImage.objects.filter(
                product=product_data.id
            ).values("original", "display_order")
            product["image"] = list(product_images)
            product_attributes = ProductAttributeValue.objects.filter(
                product=product_data.id
            ).values("attribute__name", "value_option__option")
            product["att_val"] = list(product_attributes)

            categories_data = product_data.parent.categories.values_list(
                "id", "name"
            ).distinct()
            print("categories_data:", categories_data)

            for category_id, category_name in categories_data:
                if category_id not in seen_categories:
                    category = Categories_model.objects.get(id=category_id)
                    print("category_id:", category)
                    ancestors = category.get_ancestors()
                    print("ancestors:", ancestors)
                    if ancestors:
                        showing_dict = {
                            "id": ancestors[0].id,
                            "name": ancestors[0].name,
                            "sub": {"id": category.id, "name": category.name},
                        }
                        all_categories.append(showing_dict)
                    else:
                        showing_dict = {
                            "id": category.id,
                            "name": category.name,
                        }
                        all_categories.append(showing_dict)
                    seen_categories.add(category_id)

            # Retrieve variants only for child products
            variants = Product.objects.filter(
                parent_id=product_data.id, is_public=True
            ).values(
                "id",
                "structure",
                "title",
                "description",
                "date_created",
                "date_updated",
                "stockrecords__price",
                "stockrecords__num_in_stock",
            )

            if variants:
                for variant in variants:
                    variant_id = variant["id"]
                    stock_record = StockRecord.objects.filter(
                        product_id=variant_id
                    ).values("mrp", "discount", "discount_type", "num_in_stock")
                    variant["stock_record"] = stock_record.first()
                    variant_images = ProductImage.objects.filter(
                        product=variant_id
                    ).values("original", "display_order")
                    variant["image"] = list(variant_images)
                    variant_attributes = ProductAttributeValue.objects.filter(
                        product=variant_id
                    ).values("attribute__name", "value_option__option")
                    variant["att_val"] = list(variant_attributes)
                    variant["structure"] = "child"

                product["variants"] = list(variants)

            arrayProd.append(product)

        all_categories_list = all_categories

        paginator = self.pagination_class()
        arrayProd = sorted(
            arrayProd,
            key=lambda x: (
                x.get("stock_record", {}).get("num_in_stock", 1) == 0,
                x.get("stock_record", {}).get("num_in_stock", 1),
            ),
        )
        logger.debug(f"{arrayProd=}")
        code_list = request.GET.getlist("code_list", None)
        if not code_list == None:
            try:
                arrayProd = add_voucher_details(
                    array_prod=arrayProd, code_list=code_list
                )
            except:
                pass
        paginated_data = paginator.paginate_queryset(arrayProd, request, view=self)

        response_data = {
            "categories": all_categories_list,
            "count": len(arrayProd),
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": paginated_data,
        }

        return paginator.get_paginated_response(response_data)


# recommended product api ----
class GetRecommendedProduct(APIView):

    def get(self, request, id, *args, **kwargs):
        obj = Product.objects.filter(id=id).values("recommended_products")
        # print(obj,'**********')
        # recccc_id = obj.recommended_products
        # print(recccc_id,'^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        # rec_obj = Product.objects.filter(id=recccc_id).values('id')

        arrayProd = []

        for i in obj:
            dynData = i
            category_id = i["recommended_products"]
            print(
                category_id,
                "##################################################################################",
            )
            obj1 = Product.objects.filter(id=category_id)
            obj = Product.objects.filter(id=category_id).values(
                "id",
                "title",
                "description",
                "upc",
                "is_discountable",
                "attributes__name",
                "attribute_values__value_text",
                "structure",
            )

            array = []
            price_array = []
            for index, j in enumerate(obj1):
                strategy = Selector().strategy()
                info = strategy.fetch_for_product(j)
                objprice = info.price.excl_tax
                objec = ProductImage.objects.filter(product=j.id).values("original")
                prodObj = {
                    "id": j.id,
                    "title": j.title,
                    "description": j.description,
                    "upc": j.upc,
                    "is_discountable": j.is_discountable,
                    "attributes__name": obj[index]["attributes__name"],
                    "attribute_values__value_text": obj[index][
                        "attribute_values__value_text"
                    ],
                    "price": objprice,
                    "image": objec,
                }
                array.append(prodObj)
                price_array.append(objprice)

            dynData["product"] = array

            arrayProd.append(dynData)

        return Response({"data": arrayProd})


# wishlist add api ---
WishListLine = get_model("wishlists", "Line")


@permission_classes([IsAuthenticated])
class AddProductWishlistView(APIView):
    add_product_serializer_class = AddProductWishlistSerializer
    serializer_class = WishListSerializer

    def post(self, request, *args, **kwargs):
        p_ser = self.add_product_serializer_class(data=request.data)
        user_obj = request.user
        if p_ser.is_valid():
            if not WishList.objects.filter(owner=user_obj).exists():
                wishlist = WishList()
                wishlist.owner = user_obj
                wishlist.save()
                product = p_ser.validated_data["url"]
                product_id = product.id
                wishlist.add(product)
                wishlist_obj = WishListLine.objects.filter(
                    wishlist__owner=user_obj, product=product_id
                )
                wishlist_obj.update(is_wishlist="True")
                serializer = self.serializer_class(wishlist)
                return Response(
                    {
                        "message": "product sucessfully added to wishlist",
                        "data": serializer.data,
                    }
                )
            else:
                wishlist = WishList.objects.filter(owner=user_obj).first()
                product = p_ser.validated_data["url"]
                product_id = product.id
                wishlist.add(product)
                wishlist_obj = WishListLine.objects.filter(
                    wishlist__owner=user_obj, product=product_id
                )
                wishlist_obj.update(is_wishlist="True")
                serializer = self.serializer_class(wishlist)
                return Response(
                    {
                        "message": "product sucessfully added to wishlist",
                        "data": serializer.data,
                    }
                )

        return Response({"reason": p_ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)


# get wishlist ---
WishList = get_model("wishlists", "WishList")
WishListLine = get_model("wishlists", "Line")


@permission_classes([IsAuthenticated])
class WishlistDeatailView(APIView):
    serializer = WishListDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            wishlist_obj = WishList.objects.get(owner=user)
        except WishList.DoesNotExist:
            wishlist_obj = WishList.objects.create(owner=user)
        lines = WishListLine.objects.filter(wishlist__id=wishlist_obj.id)
        serializer = self.serializer(lines, many=True, context={"request": request})
        require_data = serializer.data
        list_data = []

        for i in require_data:
            lines = WishListLine.objects.get(id=i["id"])
            dict_data = {}
            try:
                product_id = lines.product.id
            except:
                lines.delete()
                continue
            i["product_id"] = product_id
            images = ProductImage.objects.filter(product=product_id).values("original")
            i["product_images"] = images
            strategy = Selector().strategy(request=request, user=request.user)
            product = Product.objects.filter(id=product_id).first()
            i["product_category"] = Product.objects.filter(id=product_id).values(
                "categories__name"
            )
            i["stock_record"] = StockRecord.objects.filter(product=product_id).values(
                "mrp", "discount", "discount_type", "base_price", "price"
            )
            ser = PriceSerializer(
                strategy.fetch_for_product(product).price, context={"request": request}
            )
            i["product_price"] = ser.data

            # Fetch attribute values for the product if not null
            att_values = ProductAttributeValue.objects.filter(product=product_id)
            if att_values.exists():
                att_values_data = att_values.values(
                    "attribute__name", "value_option__option"
                )
                i["att_value"] = list(att_values_data)
            else:
                i["att_value"] = (
                    []
                )  # Set att_value to empty list if ProductAttributeValue is null

            list_data.append(dict_data)
        return Response(require_data)


# count of wishlist ---
WishListLine = get_model("wishlists", "Line")


@permission_classes([IsAuthenticated])
class GetCountOfWishlist(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        wishlist_count = WishListLine.objects.filter(
            wishlist__owner=self.request.user
        ).count()
        return Response({"wishlist_count": wishlist_count})


class DeleteProductFromWishlist(APIView):
    def delete(self, request, id, *args, **kwargs):
        obj = WishListLine.objects.filter(id=id)
        obj.delete()
        return Response({"message": "success"})


from apps.catalogue.models import Product
from oscar.core.loading import get_model
from rest_framework import generics
from apps.catalogue.models import Category
from django.db.models import Q
from rest_framework.response import Response
import datetime

ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")


class ListWithFilter(APIView):
    pagination_class = CustomLimitOffsetPagination

    def get(self, request, id, *args, **kwargs):

        print(f"Category ID: {id}")
        try:
            category = Category.objects.get(id=id)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
        objconcat = Product.objects.filter(categories=category, is_public=True).values(
            "id",
            "title",
            "structure",
            "description",
            "date_created",
            "stockrecords__price",
            "best_seller",
            "stockrecords__num_in_stock",
        )
        arrayProd = []
        for data in objconcat:
            dynData = data
            jjj = data["id"]

            stock_record = StockRecord.objects.filter(product=jjj).values(
                "mrp", "discount", "discount_type", "num_in_stock"
            )
            dynData["stock_record"] = stock_record.first()
            objec = ProductImage.objects.filter(product=jjj).values(
                "original", "display_order"
            )
            dynData["image"] = objec
            att_val = ProductAttributeValue.objects.filter(product=jjj).values(
                "attribute__name", "value_option__option"
            )
            dynData["att_val"] = att_val
            variants = Product.objects.filter(parent_id=jjj, is_public=True).values(
                "id",
                "structure",
                "title",
                "description",
                "date_created",
                "date_updated",
                "stockrecords__price",
                "best_seller",
                "stockrecords__num_in_stock",
            )

            if variants:
                for variant in variants:
                    variant_id = variant["id"]

                    # Fetch stock record for the child variant
                    stock_record = StockRecord.objects.filter(
                        product_id=variant_id
                    ).values("mrp", "discount", "discount_type", "num_in_stock")
                    variant["stock_record"] = (
                        stock_record.first() if stock_record else None
                    )

                    # Fetch images for the child variant
                    variant_images = ProductImage.objects.filter(
                        product=variant_id
                    ).values("original", "display_order")
                    variant["image"] = list(variant_images)

                    # Fetch attributes for the child variant
                    variant_attributes = ProductAttributeValue.objects.filter(
                        product=variant_id
                    ).values("attribute__name", "value_option__option")
                    variant["att_val"] = list(variant_attributes)
                    variant["structure"] = "child"

                # Append only child variant data
                arrayProd.extend(variants)
            else:
                pass
        #         arrayProd.append(dynData)
        filtered_arrayProd = [
            prod
            for prod in arrayProd
            if prod.get("stockrecords__price") is not None
            and prod["stockrecords__price"] > 0
        ]

        # Calculate min and max prices
        if filtered_arrayProd:
            min_product_price = min(
                prod["stockrecords__price"] for prod in filtered_arrayProd
            )
            max_product_price = max(
                prod["stockrecords__price"] for prod in filtered_arrayProd
            )
        else:
            min_product_price = None
            max_product_price = None

        attribute_filters = []
        for key, value in request.GET.items():
            if key.startswith("attr_name_") and value:
                attribute_name = value
                attribute_value_key = f"attr_value_{attribute_name}"
                attribute_values = request.GET.get(attribute_value_key)
                if attribute_values:

                    attribute_values_list = attribute_values.split(",")
                    for attribute_value in attribute_values_list:
                        attribute_filters.append(
                            {"attr_name": attribute_name, "attr_value": attribute_value}
                        )

        if attribute_filters:
            filtered_arrayProd = []
            for prod in arrayProd:
                for attribute_filter in attribute_filters:
                    filter_matched = any(
                        att_val.get("attribute__name") == attribute_filter["attr_name"]
                        and att_val.get("value_option__option")
                        == attribute_filter["attr_value"]
                        for att_val in prod.get("att_val", [])
                    )
                    if filter_matched:
                        filtered_arrayProd.append(prod)
                        break
            arrayProd = filtered_arrayProd
        # Apply price filtering
        min_price = request.GET.get("min_price")
        max_price = request.GET.get("max_price")

        def small_func(prod):
            if prod.get("stockrecords__price", 0) == None:
                return 0
            else:
                return prod.get("stockrecords__price", 0)

        def big_func(prod):
            if prod.get("stockrecords__price", float("inf")) == None:
                return float("inf")
            else:
                return prod.get("stockrecords__price", float("inf"))

        if min_price is not None:
            arrayProd = [
                prod
                for prod in arrayProd
                if float(small_func(prod=prod)) >= float(min_price)
            ]

        if max_price is not None:
            arrayProd = [
                prod for prod in arrayProd if big_func(prod=prod) <= float(max_price)
            ]

        # Sorting logic
        print(arrayProd)
        sort_by = request.GET.get("sort_by")
        if sort_by == "l2h":
            arrayProd = sorted(
                arrayProd, key=lambda x: x.get("stockrecords__price", float("inf"))
            )
        elif sort_by == "h2l":
            arrayProd = sorted(
                arrayProd,
                key=lambda x: x.get("stockrecords__price", float("-inf")),
                reverse=True,
            )
        # elif sort_by == "new_added":
        elif sort_by == "new_added" and (
            min_price is None and max_price is None
        ):  # Check if min_price or max_price is not available
            arrayProd = sorted(
                arrayProd,
                key=lambda x: x.get("date_created", datetime.datetime.min)
                or datetime.datetime.min,
                reverse=True,
            )

        # Sort to move items with stockrecords__num_in_stock == 0 to the end
        arrayProd = sorted(
            arrayProd, key=lambda x: x.get("stockrecords__num_in_stock", 0) == 0
        )
        # Apply attribute filters

        if not arrayProd:
            return Response({"data": arrayProd, "count": 0, "page_size": 0})

        paginator = self.pagination_class()
        code_list = request.GET.getlist("code_list", None)
        if not code_list == None:
            try:
                arrayProd = add_voucher_details(arrayProd, code_list=code_list)
            except:
                pass
        paginated_data = paginator.paginate_queryset(arrayProd, request, view=self)

        response_data = {
            "count": len(arrayProd),
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": paginated_data,
            "static_min_price": min_product_price,
            "static_max_price": max_product_price,
        }

        return paginator.get_paginated_response(response_data)


from rest_framework import generics
from oscar.core.loading import get_model
from django.db.models import Count
from django.db.models import Min, Max

ProductAttribute = get_model("catalogue", "ProductAttribute")


class ProductAttributeListView(generics.ListAPIView):
    pagination_class = CustomLimitOffsetPagination

    def get(self, request, *args, **kwargs):
        category_id = self.kwargs["category_id"]

        # Initialize min and max prices as None
        min_product_price = None
        max_product_price = None

        # Get parent products in the category
        parent_products = Product.objects.filter(categories=category_id)

        # Calculate min and max prices for parent products
        # parent_min_price = parent_products.aggregate(min_price=Min('stockrecords__price'))['min_price']
        # parent_max_price = parent_products.aggregate(max_price=Max('stockrecords__price'))['max_price']

        # print(parent_min_price)

        # Get child products in the category
        child_products = Product.objects.filter(parent__categories=category_id)

        # Calculate min and max prices for child products
        child_min_price = child_products.aggregate(
            min_price=Min("stockrecords__price")
        )["min_price"]
        child_max_price = child_products.aggregate(
            max_price=Max("stockrecords__price")
        )["max_price"]

        # Combine parent and child prices to get overall min and max prices
        # if parent_min_price is not None and child_min_price is not None:
        min_product_price = child_min_price
        # elif parent_min_price is not None:
        # min_product_price = parent_min_price
        # else:
        # min_product_price = child_min_price

        # if parent_max_price is not None and child_max_price is not None:
        max_product_price = child_max_price
        # elif parent_max_price is not None:
        # max_product_price = parent_max_price
        # else:
        # max_product_price = child_max_price

        result = []

        # Retrieve attributes for the given category
        queryset = (
            ProductAttribute.objects.filter(
                Q(product__categories=category_id)
                | Q(product__parent__categories=category_id)
            )
            .values("name")
            .annotate(count=Count("name"))
            .distinct()
        )

        result = []

        for item in queryset:
            attribute_name = item["name"]
            attribute_values = (
                ProductAttributeValue.objects.filter(
                    Q(attribute__name=attribute_name)
                    & Q(product__parent__categories=category_id)
                )
                .values_list("value_option__option", flat=True)
                .distinct()
            )
            attribute_name = item["name"]
            attribute_values = (
                ProductAttributeValue.objects.filter(
                    attribute__name=attribute_name, product__in=child_products
                )
                .values_list("value_option__option", flat=True)
                .distinct()
            )
            attribute_values_count = len(attribute_values)

            values_list = [
                {"value_option__option": value} for value in attribute_values
            ]

            result.append(
                {
                    "name": attribute_name,
                    "count": attribute_values_count,
                    "values": values_list,
                }
            )

        return JsonResponse(
            {
                "data": result,
                "static_min_price": min_product_price,
                "static_max_price": max_product_price,
            },
            safe=False,
        )


# shop_by_Brand

from django.http import Http404
from bannermanagement.models import Brand

# from mycustomapi.serializers.product import ProductSerializer
from .serializers import ProductWithStockSerializer

# from .serializers import ProductSerializer

att_o = get_model("catalogue", "AttributeOption")
ProductAttri = get_model("catalogue", "ProductAttributeValue")
Categories_model = get_model("catalogue", "Category")


class ShopByBrandAPIView(APIView):
    pagination_class = CustomLimitOffsetPagination
    permission_classes = [IsAuthenticated]

    def get(self, request, brand_name=None, *args, **kwargs):
        if brand_name:
            return self.get_products_by_brand(request, brand_name, *args, **kwargs)
        else:
            return self.get_brand_list()

    def get_brand_list(self):
        brands = Brand.objects.all().values("id", "brand_name", "logo")

        brand_list = []
        for brand_data in brands:
            brand = {
                "id": brand_data["id"],
                "name": brand_data["brand_name"],
                "logo": brand_data["logo"] if brand_data["logo"] else None,
            }
            brand_list.append(brand)
        return Response({"brands": brand_list})

    def get_products_by_brand(self, request, brand_name, *args, **kwargs):

        Brand_object = att_o.objects.get(option=brand_name)
        product_attri = (
            ProductAttri.objects.filter(value_option=Brand_object)
            .values_list("product_id", flat=True)
            .distinct()
        )

        products_with_name = Product.objects.filter(
            id__in=product_attri, structure="child", is_public=True
        )
        products_search_cat = Product.objects.filter(
            id__in=product_attri, structure="parent"
        )

        categories = (
            products_search_cat.exclude(categories__isnull=True)
            .values_list("categories__id", "categories__name")
            .distinct()
        )

        cat = set(categories)
        categories = list(cat)

        category_query_set = []
        showing_dict = {}
        for i in categories:
            com = Categories_model.objects.get(id=i[0])
            co = com.get_ancestors()
            try:
                showing_dict["id"] = co[0].id
                showing_dict["name"] = co[0].name
            except Exception as e:
                showing_dict["id"] = com.id
                showing_dict["name"] = com.name
                category_query_set.append(showing_dict)
                showing_dict = {}
                continue
            showing_dict["sub"] = {}
            showing_dict["sub"]["id"] = com.id
            showing_dict["sub"]["name"] = com.name
            category_query_set.append(showing_dict)
            showing_dict = {}

        print(category_query_set)

        # from .serializers import ProductSerializer

        ser = ProductWithStockSerializer(
            products_with_name, many=True, context={"request": request}
        )
        serializer_data = ser.data
        sorted_data = sorted(
            serializer_data,
            key=lambda x: (
                x.get("stock", {}).get("num_in_stock", None) == "0",
                x.get("stock", {}).get("num_in_stock", float("inf")),
            ),
        )
        logger.debug(sorted_data)
        code_list = request.GET.getlist("code_list", None)
        if not code_list == None:
            try:
                add_voucher_details(sorted_data, code_list=code_list)
            except:
                pass
        paginator = self.pagination_class()
        paginated_data = paginator.paginate_queryset(sorted_data, request, view=self)

        response_data = {
            "count": len(products_with_name),
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": paginated_data,
            "categories": category_query_set,
        }

        return paginator.get_paginated_response(response_data)


# best_seller API for FrontEND

from .serializers import BestSellerProductSerializer, FeaturedProductSerializer

# from mycustomapi.serializers.product import ProductSerializer
# from apps.catalogue.models import Product
from rest_framework.generics import ListAPIView

from oscar.core.loading import get_model
from collections import defaultdict
from django.core.exceptions import ObjectDoesNotExist

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")


class BestSellerProductListView(ListAPIView):
    serializer_class = BestSellerProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Product.objects.filter(
            best_seller=True, structure="child", is_public=True
        )[:30]

        return queryset


class FeaturedProductListView(APIView):
    serializer_class = FeaturedProductSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get all featured child products sorted by last updated date
            featured_child_products = Product.objects.filter(
                featured_products=True, structure="child"
            ).order_by("-date_created")

            # Get parent products for all featured child products to fetch categories in a batch
            parent_products = [product.parent for product in featured_child_products]
            parent_categories = Category.objects.filter(product__in=parent_products)

            # Dictionary to store products grouped by category
            category_products_dict = defaultdict(list)

            # Iterate through featured child products
            for child_product in featured_child_products:
                try:
                    parent_product = child_product.parent
                    # Get the categories for the parent product from the prefetched data
                    categories = parent_categories.filter(product=parent_product)
                    # Append child product to each category in dictionary
                    for category in categories:
                        category_products_dict[category].append(child_product)
                except ObjectDoesNotExist:
                    pass

            # List to store final results
            results = []

            # Iterate through categories and products dictionary
            for category, child_products in category_products_dict.items():
                # Ensure unique products and limit to at most 4 products per category
                unique_child_products = []
                seen_product_ids = set()
                for child_product in reversed(child_products):
                    if len(unique_child_products) >= 4:
                        break
                    if child_product.id not in seen_product_ids:
                        seen_product_ids.add(child_product.id)
                        unique_child_products.append(child_product)

                # List to store child products for this category
                category_child_products = []
                for child_product in unique_child_products:
                    product_data = {
                        "id": child_product.id,
                        "title": child_product.title,
                        "structure": child_product.structure,
                        "description": child_product.description,
                        "date_created": child_product.date_created,
                    }

                    # Retrieve stock record, images, and attribute values for the child product
                    try:
                        stock_record = StockRecord.objects.get(product=child_product)
                        product_data["stock_record"] = {
                            "mrp": stock_record.mrp,
                            "price": stock_record.price,
                            "discount": stock_record.discount,
                            "discount_type": stock_record.discount_type,
                        }
                    except ObjectDoesNotExist:
                        pass

                    product_images = ProductImage.objects.filter(
                        product=child_product
                    ).values_list("original", flat=True)
                    product_data["image"] = list(product_images)

                    product_attributes = ProductAttributeValue.objects.filter(
                        product=child_product
                    )
                    attribute_values = [
                        {
                            "attribute_name": attr.attribute.name,
                            "value": attr.value_option.option,
                        }
                        for attr in product_attributes
                    ]
                    product_data["att_val"] = attribute_values

                    # Append child product data to category products list
                    category_child_products.append(product_data)

                # Append category and child products to results list
                code_list = request.GET.getlist("code_list", None)
                if not code_list == None:
                    try:
                        category_child_products = add_voucher_details(
                            array_prod=category_child_products, code_list=code_list
                        )
                    except:
                        pass
                results.append(
                    {
                        "category": category.name,
                        "count": len(category_child_products),
                        "products": category_child_products,
                    }
                )

            return Response({"results": results})

        except Product.DoesNotExist:
            return Response("Featured products not found")


"""new line add for concept and clear"""

# class OrderSearch(APIView):

#     def get(self,request):
#         pas
from django.shortcuts import redirect


def redirect_to_dashboard(request, path=None):
    if request.user:
        return redirect("/dashboard")
    else:
        return redirect("/dashboard")


from datetime import date


class VoucherCodeAlreadyExists(APIView):
    def post(self, request):
        code_data = request.data.get("code")
        if not code_data:
            return Response(
                {"error": "Code is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            voucher_code_Alreadyused = Voucher.objects.get(code=code_data)
            print("voucher_code_Alreadyused:", voucher_code_Alreadyused)
            if not voucher_code_Alreadyused.num_orders >= 1:
                today = date.today()
                voucher_code_check = Voucher.objects.filter(
                    code=code_data,
                    voucher_set__start_datetime__lte=today,
                    voucher_set__end_datetime__gte=today,
                ).exists()
                print(
                    "code_data:", code_data, " voucher_code_exists:", voucher_code_check
                )
                if voucher_code_check:
                    return Response(
                        {"message": f"This code ({code_data}) is valid."},
                        status=status.HTTP_200_OK,
                    )
                else:
                    expire_check = Voucher.objects.filter(code=code_data).exists()
                    if expire_check:
                        return Response(
                            {"message": f"This code ({code_data}) is Expired."},
                            status=status.HTTP_200_OK,
                        )
                    return Response(
                        {"message": f"This code ({code_data}) is Invalid."},
                        status=status.HTTP_200_OK,
                    )
            else:
                return Response(
                    {"message": f"This code ({code_data}) is Already Used."}
                )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
