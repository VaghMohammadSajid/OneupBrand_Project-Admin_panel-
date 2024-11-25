from django.shortcuts import render
from rest_framework.views import APIView
from oscarapi.serializers.basket import VoucherAddSerializer, VoucherSerializer
from oscarapi.basket import operations
from oscar.apps.basket import signals
from rest_framework.response import Response
from rest_framework import status
from bannermanagement.models import VoucherSet
from django.utils.translation import gettext_lazy as _
from bannermanagement.models import VoucherSet
from .serializer import VoucherRemoveSerializer
from rest_framework.permissions import IsAuthenticated

# from apps.catalogue.models import Product
from oscar.core.loading import get_model
import logging

logger = logging.getLogger(__name__)
from itertools import chain


model_of_product = get_model("catalogue", "Product")
# Create your views here.


class AddVoucherView(APIView):
    """
        Add a voucher to the basket.

        POST(vouchercode)
        {
            "vouchercode": "kjadjhgadjgh7667"
        }
    from oscar.apps.basket import signals    Will return 200 and the voucher as json if successful.
        If unsuccessful, will return 406 with the error.

    """

    add_voucher_serializer_class = VoucherAddSerializer
    serializer_class = VoucherSerializer

    def post(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin
        v_ser = self.add_voucher_serializer_class(
            data=request.data, context={"request": request}
        )

        if v_ser.is_valid():

            basket = operations.get_basket(request)

            voucher = v_ser.instance
            try:
                the_voucher_checking = VoucherSet.objects.get(
                    voucher=voucher.voucher_set
                )
            except:
                return Response(
                    {"succes": False, "message": "Voucher Doesn't exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not the_voucher_checking.clubable:
                if basket.vouchers.all().exists():
                    return Response("voucher is not clubable")
            else:
                if the_voucher_checking.amount_type == "Absolute":
                    voucher_con = the_voucher_checking.condition
                    basket_value = basket.total_excl_tax
                    if voucher_con.min_value > basket_value:
                        return Response({"msg":f"You need to have minimum {voucher_con.min_value} in the cart"},status=status.HTTP_400_BAD_REQUEST)
                if the_voucher_checking.amount_type == "Percentage":
                    voucher_con = the_voucher_checking.condition
                    basket_value = basket.total_excl_tax
                    if voucher_con.min_value > basket_value:
                        return Response({"msg":f"You need to have minimum value {voucher_con.min_value} in the cart"},status=status.HTTP_400_BAD_REQUEST)
                    if voucher_con.max_value > basket_value:
                        return Response({"msg":f"You can only have maximum value {voucher_con.min_value} in the cart"},status=status.HTTP_400_BAD_REQUEST)

 
                min_club = None
                for single_voucher in basket.vouchers.all():
                    vo_check_set = VoucherSet.objects.get(
                        voucher=single_voucher.voucher_set
                    )
                    logger.debug(
                        f"{vo_check_set.clubable=} {vo_check_set.club_number=}"
                    )
                    if vo_check_set.clubable and min_club == None:
                        min_club = int(vo_check_set.club_number)

                    elif min_club == None:
                        return Response("non clubable voucher included in the basket")
                    elif min_club > int(vo_check_set.club_number):
                        min_club = int(vo_check_set.club_number)
                logger.debug(f"{min_club=}")

                if not min_club == None and min_club <= basket.vouchers.all().count():
                    return Response("maximum number of clubable voucher reached")
                if (
                    int(the_voucher_checking.club_number)
                    <= basket.vouchers.all().count()
                ):
                    return Response(
                        f"this voucher can only club with {the_voucher_checking.club_number} vouchers"
                    )

            try:
                logger.debug(voucher.name)
                logger.debug(VoucherSet.objects.all())
                for i in VoucherSet.objects.all():
                    logger.debug(i.vouchername)
                    logger.debug(i.voucher)
                logger.debug(voucher.name)
                voucher_set = VoucherSet.objects.get(voucher=voucher.voucher_set)
            except Exception as e:
                import traceback

                f = traceback.format_exc()
                logger.debug(f"{f=}")
                return Response("corrupted voucher contact voucher distributer")

            if basket.vouchers.all().exists():
                single_test_voucher = basket.vouchers.all()[0]
                check_voucher_set = single_test_voucher.voucher_set
                vo_check_set = VoucherSet.objects.get(voucher=check_voucher_set)
                if not vo_check_set.voucher_type == voucher_set.voucher_type:
                    return Response("can't mix different type of vouchers")

            if voucher in basket.vouchers.all():
                return Response("this voucher already exist in your voucher list")

            flag = None
            create_flag = None

            if voucher.offers.all().exists():
                try:
                    for single_offer in voucher.offers.all():
                        if single_offer.condition.range.back_range:
                            range_object = single_offer.condition.range.back_range

                            all_lines = basket.lines.all().values_list("product")
                            logger.debug(all_lines)
                            flattened_list = list(chain.from_iterable(all_lines))

                            if range_object._all_product.filter(
                                id__in=flattened_list
                            ).count() == len(flattened_list):
                                flag = 1
                                create_flag = 1
                                break
                        else:
                            flag = 0
                except:
                    flag = 0
            if flag == 0:
                for single_offer in voucher.offers.all():
                    if single_offer.condition.range.includes_all_products:
                        create_flag = 1
                        continue
                    range = single_offer.condition.range
                    for single_line in basket.all_lines():
                        logger.debug(single_line.product)
                        if not range.contains_product(single_line.product):
                            return Response(
                                f"{single_line.product.title} not included in the voucher"
                            )

                create_flag = 1

            if create_flag == 1:
                basket.vouchers.add(voucher)
                res = {
                    "name": voucher.name,
                    "code": voucher.code,
                }

                # return Response("nice")
                signals.voucher_addition.send(
                    sender=None, basket=basket, voucher=voucher
                )
                return Response(res, status=status.HTTP_201_CREATED)
            else:
                return Response(f"some Products in the cart not included in voucher")

        else:
            print(v_ser.errors["non_field_errors"][0])
            return Response(
                v_ser.errors["non_field_errors"][0],
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )


class RemoveVoucherApi(APIView):

    remove_voucher_serializer_class = VoucherRemoveSerializer
    serializer_class = VoucherSerializer

    def post(self, request):

        try:
            v_ser = self.remove_voucher_serializer_class(
                data=request.data, context={"request": request}
            )
            if v_ser.is_valid():
                try:
                    voucher = v_ser.instance
                    basket = operations.get_basket(request)
                    basket.vouchers.remove(voucher)
                    print(f"{basket.vouchers.all()=}")
                    res = {
                        "voucher": {
                            "name": voucher.name,
                            "code": voucher.code,
                        },
                        "details": "voucher removed",
                    }

                    return Response(res, status=status.HTTP_200_OK)
                except:
                    return Response("problem with the remove api contanct developer")
        except:
            pass
        return Response("validation error")


class VoucherValidator(APIView):

    def post(self, request):
        basket = operations.get_basket(request=request)
        all_vouchers = basket.vouchers.all()
        for i in all_vouchers:
            if i.num_orders > 0:
                return Response("voucher has been used", status=status.HTTP_200_OK)
        # print(basket.vouchers.all())
        return Response("all check has  passed", status=status.HTTP_200_OK)


Category = get_model("catalogue", "Category")


class CategoryList(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.filter(depth=1)
        all_category_list = []
        for i in categories:
            single_category_dict = {"category_id": i.id, "category_name": i.name}

            child = return_child_dict(i)
            single_category_dict["child"] = child
            all_category_list.append(single_category_dict)
            
            predefined_list = ['Apparels','Accessories','Personal Care','Home & Decor','Furnishing','Kitchenware','Appliances','Gadgets','Electronics','Gifting']
            ordered_categories = sorted(all_category_list, key=lambda x: predefined_list.index(x['category_name']) if x['category_name'] in predefined_list else len(predefined_list))
    
        return Response({"list": ordered_categories}, status=status.HTTP_200_OK)


def return_child_dict(main_query):
    return main_query.get_descendants().values("id", "name")


import requests
import json


class SendStatus(APIView):
    def get(self, request):
        model_data = model_of_product.objects.all().values_list("upc", flat=True)
        logger.debug(model_data)
        ERP_URL = "https://oneuperp.stackerbee.com/api/method/django_ecommerce.api.update_item_status"
        HEADERS = {
            "Authorization": "token b338acdcc391620:c1391947f4a80ab",
            "Content-Type": "application/json",
        }
        data = list(model_data)
        logger.debug(data)
        # response = requests.post(url=ERP_URL, headers=HEADERS,json={"item_code":data})
        # logger.debug(response)
        # logger.debug(response.json())

        return Response({"model": data})
