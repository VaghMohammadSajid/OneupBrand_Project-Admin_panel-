from oscar.core.loading import get_model
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
from django.utils import timezone
from wallet.models import Wallet
from cart_api.models import Freeze
from django.conf import settings

from apps.order.models import OrderJson
from credit.models import Credit, CreditHistory
from whatsapp.views import SendMessage
from useraccount.models import ClientDetails
from homepageapi.utils import voucher_calculation, voucher_calc_in_cart
from oneup_project.settings import ERP_TOKEN,ERP_URL


from rest_framework import generics, response, status, views

from mycustomapi.basket.operations import request_allows_access_to_basket
from mycustomapi.permissions import IsOwner
from mycustomapi.utils.loading import get_api_classes
from mycustomapi.signals import oscarapi_post_checkout
from mycustomapi.views.utils import parse_basket_from_hyperlink
from rest_framework.views import APIView
from apps.address.models import *
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.order.models import Razorpay
from mycustomapi.serializers.checkout import OrderSerializer as Ors
from mycustomapi.serializers.checkout import CheckoutSerializer as Ches
from homepageapi.serializers import BasketSerializer
from homepageapi.utils import create_voucher_data
from oscarapi.basket import operations
import requests
from django.db.models import Count
from ..serializers.checkout import VoucherListSerializer
from ..serializers.checkout import (
    ShipAddressSerializer,
    BillingAddressSerializer,
    BillAddressSerializer,
)
from send_email.utils import send_order_confirmation_email
from apps.basket.models import ShippinCharge
from apps.basket.models import ShippinCharge
from useraccount.models import UserAuthTokens, UserProfile, ClientDetails, OTP
from django.contrib.auth.models import User
from apps.partner.models import StockRecord
from django.views import View
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from oneup_project import settings
from DiscountManagement.models import GiftCartTotalAMount

logger = logging.getLogger(__name__)

Order = get_model("order", "Order")
Voucher = get_model("voucher", "Voucher")
PaymentEventType = get_model("order", "PaymentEventType")
PaymentEvent = get_model("order", "PaymentEvent")

OrderLine = get_model("order", "Line")
OrderLineAttribute = get_model("order", "LineAttribute")
ShippingEvent = get_model("order", "ShippingEvent")
UserAddress = get_model("address", "UserAddress")
ShippingEventQuantity = get_model("order", "ShippingEventQuantity")
(
    CheckoutSerializer,
    OrderLineAttributeSerializer,
    OrderLineSerializer,
    OrderSerializer,
    UserAddressSerializer,
) = get_api_classes(
    "serializers.checkout",
    [
        "CheckoutSerializer",
        "OrderLineAttributeSerializer",
        "OrderLineSerializer",
        "OrderSerializer",
        "UserAddressSerializer",
    ],
)

__all__ = (
    "CheckoutView",
    "OrderList",
    "OrderDetail",
    "OrderLineList",
    "OrderLineDetail",
    "OrderLineAttributeDetail",
    "UserAddressList",
    "UserAddressDetail",
)


class BetterDictFormatter(logging.Formatter):
    def format(self, record):
        if isinstance(record.msg, dict):
            formatted_msg = "Dictionary contents:\n"
            for key, value in record.msg.items():
                formatted_msg += f"{key}: {value}\n"
            record.msg = formatted_msg
        return super().format(record)


class Orderstatusdetails(APIView):
    def get(self, request):
        distinct_statuses = Order.objects.values("status").distinct()
        unique_statuses = list(
            {
                status_dict["status"]: status_dict
                for status_dict in distinct_statuses
                if status_dict["status"] != ""
            }.values()
        )
        print("status_values", unique_statuses)
        return Response(data=unique_statuses, status=status.HTTP_200_OK)


class OrderList(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = (IsOwner,)

    def get(self, request):
        user = request.user
        data = (
            Order.objects.filter(user=user)
            .annotate(product_count=Count("basket__lines"))
            .values(
                "product_count",
                "number",
                "date_placed",
                "status",
                "total_incl_tax",
                "billing_address",
                "shipping_address__line1",
                "payment_types",
                "user__username",
            )
            .order_by("-date_placed")
        )
        print("response of orders", data)
        return Response(data=data, status=status.HTTP_200_OK)

    def post(self, request):
        operation = request.data.get("operations", [])
        duration = request.data.get("duration", "")
        user = request.user
        if duration and operation:
            # Calculate the start date based on the provided duration
            end_date = timezone.now()
            start_date = end_date - timedelta(days=int(duration))
            data = (
                Order.objects.filter(
                    user=user, status__in=operation, date_placed__gte=start_date
                )
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count",
                    "number",
                    "date_placed",
                    "status",
                    "total_incl_tax",
                    "billing_address",
                    "shipping_address__line1",
                    "payment_types",
                    "user__username",
                )
                .order_by("-date_placed")
            )
            return Response(data=data, status=status.HTTP_200_OK)
        elif duration:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=int(duration))
            data = (
                Order.objects.filter(user=user, date_placed__gte=start_date)
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count",
                    "number",
                    "date_placed",
                    "status",
                    "total_incl_tax",
                    "billing_address",
                    "shipping_address__line1",
                    "payment_types",
                    "user__username",
                )
                .order_by("-date_placed")
            )
            return Response(data=data, status=status.HTTP_200_OK)
        elif operation:
            data = (
                Order.objects.filter(user=user, status__in=operation)
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count",
                    "number",
                    "date_placed",
                    "status",
                    "total_incl_tax",
                    "billing_address",
                    "shipping_address__line1",
                    "payment_types",
                    "user__username",
                )
                .order_by("-date_placed")
            )
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            data = (
                Order.objects.filter(user=user)
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count",
                    "number",
                    "date_placed",
                    "status",
                    "total_incl_tax",
                    "billing_address",
                    "shipping_address__line1",
                    "payment_types",
                    "user__username",
                )
                .order_by("-date_placed")
            )
            return Response(data=data, status=status.HTTP_200_OK)


class OrderListwithoutlogin(generics.ListAPIView):

    def post(self, request):
        operation = request.data.get("operations", [])
        duration = request.data.get("duration", "")
        mobile_number = request.data.get("mobilenumber", "")
        usrprofile_obj = UserProfile.objects.filter(mobile_number=mobile_number)
        if usrprofile_obj.exists():
            user_details = usrprofile_obj.first()
            user = User.objects.get(username=user_details.mobile_number)
        if duration and operation:
            # Calculate the start date based on the provided duration
            end_date = timezone.now()
            start_date = end_date - timedelta(days=int(duration))
            data = (
                Order.objects.filter(
                    user=user, status__in=operation, date_placed__gte=start_date
                )
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count", "number", "date_placed", "status", "total_incl_tax"
                )
                .order_by("-date_placed")
            )
            return Response(data=data, status=status.HTTP_200_OK)
        elif duration:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=int(duration))
            data = (
                Order.objects.filter(user=user, date_placed__gte=start_date)
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count", "number", "date_placed", "status", "total_incl_tax"
                )
                .order_by("-date_placed")
            )
            return Response(data=data, status=status.HTTP_200_OK)
        elif operation:
            data = (
                Order.objects.filter(user=user, status__in=operation)
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count", "number", "date_placed", "status", "total_incl_tax"
                )
                .order_by("-date_placed")
            )
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            data = (
                Order.objects.filter(user=user)
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count", "number", "date_placed", "status", "total_incl_tax"
                )
                .order_by("-date_placed")
            )
            return Response(data=data, status=status.HTTP_200_OK)


class OrderDetail(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsOwner,)


class OrderLineList(generics.ListAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        user = self.request.user
        return super().get_queryset().filter(order_id=pk, order__user=user)


class OrderLineDetail(generics.RetrieveAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer

    def get_queryset(self):
        return super().get_queryset().filter(order__user=self.request.user)


class OrderLineAttributeDetail(generics.RetrieveAPIView):
    queryset = OrderLineAttribute.objects.all()
    serializer_class = OrderLineAttributeSerializer


from django.contrib.auth import logout
from useraccount.models import VocherLoginConnect
from useraccount.sms import SmsOtpIntegration
from ..serializers.checkout import OrderSerializerForRetry

from sync_data_erp.models import FailedOrder


def failed_order_retry():
    for single_failed_order in FailedOrder.objects.all():
        logger.debug(f"starting the order {single_failed_order.order_number}")
        try:
            order_id = single_failed_order.order_number
            order = Order.objects.prefetch_related("lines").get(number=order_id)
            logger.debug(order.__dict__)
            logger.debug(order.lines.all().values())
            order_data = OrderSerializerForRetry(order).data
            (
                voucher_list,
                total_offer_,
                gst_payable_for_voucher,
                basic_amount_radeemable,
                total_tax,
                total_discount,
                balance_payable,
                shiping_charge_in_voucher,
            ) = create_voucher_data(basket=order.basket)
            shiping = ShippinCharge.objects.get(basket=order.basket)
            logger.debug(f" order data in retry {order_data=}")
        except:
            # import traceback

            # f = traceback.format_exc()
            # logger.debug(order_id)
            # logger.debug(f"{f=}")
            logger.error("error in cron order",exc_info=True)
            continue
        try:
            serve_order_to_erp(
                basket=order.basket,
                order=order,
                voucher_list=voucher_list,
                shiping=shiping,
                order_data=order_data,
                total_offer=total_offer_,
                basic_amount_radeemable=basic_amount_radeemable,
            )
        except Exception as e:
            # subject = "Error in Processing Order Payment Type"
            # sender = settings.EMAIL_HOST_USER
            # # send_mail(subject, str(e), sender, ["pranavpranab@gmail.com"])
            # import traceback

            # f = traceback.format_exc()
            # logger.debug(f"{f=}")
            # logger.debug(f"starting the order 2 {order_id}")
            continue
        logger.debug(f"starting the order 3 {order_id}")
        single_failed_order.delete()


from django.shortcuts import render


def failed_order_view(request):
    failed_order = FailedOrder.objects.all()
    return render(request, "import/failed_order.html", {"order": failed_order})


class CheckoutView(views.APIView):

    basket_ser = BasketSerializer
    """
    Prepare an order for checkout.

    POST(basket, shipping_address,
         [total, shipping_method_code, shipping_charge, billing_address]):
    {
        "basket": "http://testserver/oscarapi/baskets/1/",
        "guest_email": "foo@example.com",
        "total": "100.0",
        "shipping_charge": {
            "currency": "EUR",
            "excl_tax": "10.0",
            "tax": "0.6"
        },
        "shipping_method_code": "no-shipping-required",
        "shipping_address": {
            "country": "http://127.0.0.1:8000/oscarapi/countries/NL/",
            "first_name": "Henk",
            "last_name": "Van den Heuvel",
            "line1": "Roemerlaan 44",
            "line2": "",
            "line3": "",
            "line4": "Kroekingen",
            "notes": "Niet STUK MAKEN OK!!!!",
            "phone_number": "+31 26 370 4887",
            "postcode": "7777KK",
            "state": "Gerendrecht",
            "title": "Mr"
        }
        "billing_address": {
            "country": country_url,
            "first_name": "Jos",
            "last_name": "Henken",
            "line1": "Boerderijstraat 19",
            "line2": "",
            "line3": "",
            "line4": "Zwammerdam",
            "notes": "",
            "phone_number": "+31 27 112 9800",
            "postcode": "6666LL",
            "state": "Gerendrecht",
            "title": "Mr"
         }
    }
    returns the order object.
    """

    order_serializer_class = Ors
    serializer_class = Ches
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None, *args, **kwargs):
        # TODO: Make it possible to create orders with options.
        # at the moment, no options are passed to this method, which means they
        # are also not created.

        basket = parse_basket_from_hyperlink(request.data, format)
        gift = False

        print("@#%#$%#$^@#$%@#%#$%!@#$@#%#$%#$", basket)
        baskets = operations.get_basket(request)
        for i in baskets.lines.all():
            stock_status, report = i.purchase_info.availability.is_purchase_permitted(
                i.quantity
            )
            if not stock_status:
                return Response({"status": f"{report} for {i.product.title}"})
        if VocherLoginConnect.objects.filter(user=request.user).exists():
            if not baskets.vouchers.all().exists():
                return Response(
                    {"detail": "can't checkout"}, status=status.HTTP_401_UNAUTHORIZED
                )

        if not request_allows_access_to_basket(request, basket):
            return response.Response(
                "Unauthorized", status=status.HTTP_401_UNAUTHORIZED
            )

        c_ser = self.serializer_class(data=request.data, context={"request": request})

        if c_ser.is_valid():

            print(c_ser.instance)
            order = c_ser.save()
            ser = self.basket_ser(baskets, context={"request": request})
            cart = ser.data
            tota_amount_in_cart = cart["total_incl_tax_excl_discounts"]
            (
                voucher_list,
                total_offer_,
                gst_payable_for_voucher,
                basic_amount_radeemable,
                total_tax,
                total_discount,
                balance_payable,
                shiping_charge_in_voucher,
            ) = create_voucher_data(basket=basket)
            logger.debug(
                f" offer in checkout{total_offer_=} {gst_payable_for_voucher=} {basic_amount_radeemable=} {balance_payable=}"
            )
            tota_amount_to_pay = round(float(balance_payable), 2)
            ship_include_status = any(
                [d.get("shipping_incl", False) for d in voucher_list]
            )
            try:
                gift_obj = GiftCartTotalAMount.objects.get(cart=basket)
                tota_amount_to_pay = gift_obj.total_amount
                tota_amount_in_cart = tota_amount_to_pay
                gift = True
            except:
                import traceback

                f = traceback.format_exc()
                logger.error(f"error in checkout for gift total calc{f=}")
                # import pdb;pdb.set_trace()
            try:
                if not int(shiping_charge_in_voucher) == None:
                    shiping = ShippinCharge.objects.get(basket=basket)
                    shiping.charge = shiping_charge_in_voucher
                    shiping.save()
                else:
                    shiping = ShippinCharge.objects.get(basket=basket)
            except:
                shiping = ShippinCharge.objects.get(basket=basket)

            if not ship_include_status:
                if gift == True:
                    order.total_incl_tax = tota_amount_to_pay + float(
                        round(shiping.charge, 2)
                    )
                    logger.debug("inside gift")
                elif float(basic_amount_radeemable) - float(total_offer_) >= 0:
                    order.total_incl_tax = (
                        float(tota_amount_in_cart)
                        - float(total_offer_)
                        + float(round(shiping.charge, 2))
                    )
                    logger.debug("inside gift elif")
                else:
                    order.total_incl_tax = balance_payable + float(
                        round(shiping.charge, 2)
                    )
                    logger.debug("inside gift else")
            else:
                if gift == True:
                    order.total_incl_tax = tota_amount_to_pay + float(
                        round(shiping.charge, 2)
                    )
                    logger.debug("inside else gift")
                elif float(tota_amount_to_pay) + float(shiping.charge) >= 0:

                    if total_offer_ > basic_amount_radeemable:
                        logger.debug("inside else elife if")
                        remaining_amount = total_offer_ - basic_amount_radeemable
                        if remaining_amount > float(round(shiping.charge, 2)):
                            logger.debug("inside else elife if if")
                            order.total_incl_tax = tota_amount_to_pay
                        else:
                            logger.debug("inside else elife else")
                            order.total_incl_tax = tota_amount_to_pay + (
                                float(round(shiping.charge, 2)) - remaining_amount
                            )
                    else:
                        logger.debug(f"{total_offer_=}")
                        order.total_incl_tax = tota_amount_to_pay + float(
                            round(shiping.charge, 2)
                        )
                else:
                    order.total_incl_tax = 0
            order.status = "Order Created"

            order.shipping_incl_tax = float(round(shiping.charge, 2))
            order.save()

            for i in PaymentEvent.objects.filter(order=order):
                print("before raz", i.__dict__)
            try:
                if order.payment_types == "Razorpay":

                    Razorpay.objects.create(
                        payment_id=request.data.get("payment_id"),
                        order_id=order,
                        total_amount=request.data.get("total_amount"),
                        status=request.data.get("status"),
                    )
                    try:
                        try:
                            event_type = PaymentEventType.objects.get(
                                name=request.data.get("status")
                            )
                        except Exception as e:
                            event_type = PaymentEventType.objects.create(
                                name=request.data.get("status")
                            )
                        PaymentEvent.objects.create(
                            order=order,
                            amount=request.data.get("total_amount"),
                            event_type=event_type,
                            reference="Razorpay",
                        )
                    except Exception as e:
                        pass
            except:
                order.delete()
                return Response({"detail": "razorpay issue"})

            try:
                if order.payment_types == "Credit":

                    wallet = Credit.objects.get(user=request.user)
                    amount = wallet.get_amount()
                    if amount < request.data.get("total_amount"):
                        order.delete()
                        return Response(
                            {
                                "status": "Not enough amount in Credit try adding online pay with Credit"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    wallet.remove_amount(request.data.get("total_amount"), order=order)

                    try:
                        try:
                            event_type = PaymentEventType.objects.get(
                                name=request.data.get("status")
                            )
                        except Exception as e:
                            event_type = PaymentEventType.objects.create(
                                name=request.data.get("status")
                            )

                        PaymentEvent.objects.create(
                            order=order,
                            amount=request.data.get("total_amount"),
                            event_type=event_type,
                            reference="Credit",
                        )

                    except Exception as e:
                        pass
            except:
                order.delete()
                return Response({"detail": "Credit issue"})

            try:
                if order.payment_types == "Custome":
                    wallet = Credit.objects.get(user=request.user)
                    amount = request.data.get("credit_amount")
                    raz_amount = order.total_incl_tax - int(amount)
                    wallet.remove_amount(
                        int(request.data.get("credit_amount")), order=order
                    )
                    try:
                        try:
                            event_type = PaymentEventType.objects.get(
                                name=request.data.get("status")
                            )
                        except Exception as e:
                            event_type = PaymentEventType.objects.create(
                                name=request.data.get("status")
                            )

                        PaymentEvent.objects.create(
                            order=order,
                            amount=amount,
                            event_type=event_type,
                            reference="Credit",
                        )
                        PaymentEvent.objects.create(
                            order=order,
                            amount=raz_amount,
                            event_type=event_type,
                            reference="Razorpay",
                        )

                    except Exception as e:
                        pass
            except Exception as e:
                import traceback

                traceback.print_exc()
                order.delete()
                return Response(
                    {"custome pay failed"}, status=status.HTTP_400_BAD_REQUEST
                )

            basket.freeze()
            o_ser = self.order_serializer_class(order, context={"request": request})

            resp = response.Response(o_ser.data)
            order_data = o_ser.data
            print(type(order_data))

            order_data["voucher_list"] = voucher_list
            order_data["offer_tootal_amount"] = total_offer_

            order_data["total_gst_payable"] = gst_payable_for_voucher

            oscarapi_post_checkout.send(
                sender=self,
                order=order,
                user=request.user,
                request=request,
                response=resp,
            )

            save_basket = True
            for single_line in order.lines.all():
                single_line.stockrecord.consume_allocation(
                    quantity=single_line.quantity
                )
                if save_basket:
                    Freeze.objects.filter(cart=basket).delete()
                    save_basket = False
            try:
                logger.debug(f"billing address debug {order_data=}")
                serve_order_to_erp(
                    basket=basket,
                    order_data=order_data,
                    order=order,
                    shiping=shiping,
                    voucher_list=voucher_list,
                    total_offer=total_offer_,
                    basic_amount_radeemable=basic_amount_radeemable,
                )
            except Exception as e:
                pass
                # subject = "Error in Processing Order Payment Type"
                # sender = settings.EMAIL_HOST_USER
                # send_mail(subject, str(e), sender, ["pranavpranab@gmail.com"])
                import traceback

                f = traceback.format_exc()
                from sync_data_erp.models import FailedOrder

                FailedOrder.objects.create(
                    order_number=order.number, order_failed_trace_back=str(f)
                )

            try:
                try:
                    import json

                    json_data = order_data
                    first_name = json_data["shipping_address"]["first_name"]
                    last_name = json_data["shipping_address"]["last_name"]

                    fullname = f"{first_name} {last_name}"

                    mobile_number = json_data["shipping_address"]["phone_number"]
                    ordernumber = order
                    SmsOtpIntegration.send_otp_sms_checkout(
                        mobile_number, fullname, ordernumber
                    )
                    obj = SendMessage()
                    logger.debug(f"{mobile_number=} {fullname=} {ordernumber}")
                    obj.send_whatsapp_message(
                        mobile_no=mobile_number, name=fullname, order_id=ordernumber
                    )

                except Exception as e:
                    logger.critical(e)
                    import traceback

                    f = traceback.format_exc()
                    logger.critical(f)

                send_order_confirmation_email(order=order, total_offer_=total_offer_)
            except Exception as e:
                print(e)
            return resp

        return response.Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)


from apps.order.models import StatusReprotOrderErpToAdmin


def serve_order_to_erp(
    basket,
    order_data,
    order,
    shiping,
    voucher_list,
    total_offer,
    basic_amount_radeemable,
):
    file_handler = logging.FileHandler("app.log")
    formatter = BetterDictFormatter()
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    total_breadth = 0
    total_weight = 0
    total_height = 0
    total_length = 0
    try:
        voucher_calc = voucher_calculation(
            basket=basket,
            basic_amount_radeemable=basic_amount_radeemable,
            total_offer_amount=total_offer,
            order=order,
            shipping=shiping.charge,
        )
    except:
        import traceback

        f = traceback.format_exc()
        logger.error(f"error in voucher calc for gift vouchers {f=}")
        voucher_calc = []

    user = basket.owner

    try:
        ClientDetails.objects.get(user=user)
        user_type = "client"
    except Exception as e:

        user_type = "voucher"

    for single_line in basket.lines.all():

        total_weight = total_weight + (
            single_line.stockrecord.weight * single_line.quantity
        )
        total_length = total_length + (
            single_line.stockrecord.length * single_line.quantity
        )
        total_height = total_height + (
            single_line.stockrecord.height * single_line.quantity
        )
        total_breadth = total_breadth + (
            single_line.stockrecord.breadth * single_line.quantity
        )
    url = f"{ERP_URL}api/method/django_ecommerce.api.sync_orders"
    try:
        token = ERP_TOKEN
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }
        import json

        json_data = order_data

        dict_of_data = {
            "name": json_data["shipping_address"]["first_name"]
            + " "
            + json_data["shipping_address"]["last_name"],
            "customer_id": order.user.use.unique_string,
            "shipping_name": json_data["shipping_address"]["first_name"]
            + " "
            + json_data["shipping_address"]["last_name"],
            "customer_type": user_type,
            "billing_address_id": json_data["billing_address"]["id"],
            "billing_city": json_data["billing_address"]["line4"],
            "billing_state": json_data["billing_address"]["state"],
            "billing_country": "India",
            "billing_phone": json_data["billing_address"]["phone_number"],
            "billing_address": f"{ json_data['billing_address']['line1'] }  { json_data['billing_address']['line2'] } {json_data['billing_address']['line3']} {json_data['billing_address']['line4']}",
            "billing_email": json_data["billing_address"]["email"],
            "billing_pincode": json_data["billing_address"]["postcode"],
            "billing_name": json_data["billing_address"]["first_name"]
            + " "
            + json_data["billing_address"]["last_name"],
            "number": json_data["number"],
            "payment_method": order.payment_types,
            "express_type": "Surface",
            "shipment_weight": float(total_weight),
            "shipment_width": float(total_breadth),
            "shipment_length": float(total_length),
            "shipment_height": float(total_height),
            "shipping_charge": float(shiping.charge),
            "courier_id": shiping.courier_id,
            "city": json_data["shipping_address"]["line4"],
            "state": json_data["shipping_address"]["state"],
            "country": "India",
            "phone": json_data["shipping_address"]["phone_number"],
            "address": f"{ json_data['shipping_address']['line1'] }  { json_data['shipping_address']['line2'] } {json_data['shipping_address']['line3']} {json_data['shipping_address']['line4']}",
            "email": json_data["email"],
            "pincode": json_data["shipping_address"]["postcode"],
            "address_id": order.shipping_address.id,
        }
        product_details = []
        single_product_dict = {}
        for i in json_data["lines"]:
            data_product = i["product"]
            single_product_dict["item"] = data_product["upc"]
            single_product_dict["quantity"] = i["quantity"]
            stock = StockRecord.objects.get(product__id=data_product["id"])
            single_product_dict["price"] = float(stock.price)
            single_product_dict["upc"] = data_product["upc"]
            single_product_dict["shipment_weight"] = float(stock.weight)
            single_product_dict["shipment_width"] = float(stock.breadth)
            single_product_dict["shipment_length"] = float(stock.length)
            single_product_dict["shipment_height"] = float(stock.height)
            single_product_dict["get_base_price"] = round(
                float(stock.get_base_price()), 2
            )
            single_product_dict["gst_value"] = round(
                float(stock.calculate_gst_value()), 2
            )

            product_details.append(single_product_dict)
            single_product_dict = {}
        dict_of_data["order_items"] = product_details
        dict_of_data["voucher_list"] = voucher_list
        dict_of_data["total_offer_value"] = total_offer
        dict_of_data["final_price_after_voucher_applied"] = float(
            order_data["total_incl_tax"]
        )
        dict_of_data["voucher_calc_for_gift_vouchers"] = voucher_calc

        try:
            if order.payment_types == "Custome":
                creditamount = CreditHistory.objects.get(order=order)
                dict_of_data["credit_amount"] = creditamount.credit_used_amount * -1
                dict_of_data["credit_type"] = creditamount.credit.credit_gst
                dict_of_data["credit_shipping_type"] = (
                    creditamount.credit.credit_shipping_type
                )
        except Exception as e:
            pass
            # subject = "Error in Processing Order Payment Type"
            # sender = settings.EMAIL_HOST_USER
            # send_mail(subject, str(e), sender, ["pranavpranab@gmail.com"])

        final_dict = {"data": [dict_of_data]}
        final_json = json.dumps(final_dict)
        logger.debug(f"Order json sending into erp {final_dict}")

        OrderJson.objects.create(order=order, order_json=final_dict)

        response_post = requests.post(url, data=final_json, headers=headers)
        try:
            logger.debug(response_post)
            logger.debug(response_post.__dict__)
            logger.debug(order.number)
            data = response_post.json()
        except:
            logger.debug(response_post)
            raise Exception("Order failed in erp")
        try:
            if not data["message"] == "Successfully Created Customer and Sales Orders":
                raise Exception("Order failed in erp")
        except:
            logger.debug(f"{json_data['billing_address']=}")
            raise Exception("Order failed in erp")

        order.erp_status = "Send To ERP"
        order.save()

        StatusReprotOrderErpToAdmin.objects.create(
            order_id=order.number, new_status="Send To ERP"
        )

    except Exception as e:
        import traceback

        f = traceback.format_exc()
        logger.debug(f"{f}")
        logger.debug(f"{json_data['billing_address']=}")

        raise Exception("flow to erp stopped")


class WalletTotalAmountAPi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            wallet = Wallet.objects.get(user=user)
            amount = wallet.get_amount()
            return Response({"amount": amount}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            import traceback

            traceback.print_exc()
            return Response({"error": "error"}, status=status.HTTP_400_BAD_REQUEST)


class UserAddressList(generics.ListCreateAPIView):
    permission_classes = (IsOwner,)

    serializer_class = UserAddressSerializer

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user).order_by("id")


class UserAddressDetail(generics.RetrieveUpdateDestroyAPIView):

    permission_classes = (IsOwner,)
    serializer_class = UserAddressSerializer

    def get_queryset(self):
        return UserAddress.objects.filter(user=self.request.user)


# class GetPostCodeInformation(APIView):

#     #permission_classes = [IsAuthenticated]
#     def get(self,request):
#         postal_code = request.query_params.get('postal_code')


#         geolocator = Nominatim(user_agent="oneup")

#         zipcode = str(postal_code)

#         location = geolocator.geocode(zipcode)
#         if location:

#             address = str(location)
#             print(address)
#             add_list = address.split(',')
#             data = {}
#             data['postal_code'] = add_list[1]
#             data['city'] = add_list[0]
#             data['district'] = add_list[2]

#             data['state'] = add_list[-2]
#             data['country'] = add_list[-1]
#             return Response(data)

#         else:
#             return Response({"message":"Invalid postal code"},status = status.HTTP_400_BAD_REQUEST)


import requests


# new api for postal address
class GetPostCodeInformation(APIView):

    def get_address_details(self, pincode):
        url = f"https://api.postalpincode.in/pincode/{pincode}"
        response = requests.get(url)
        data = response.json()
        if data[0]["Status"] == "Success":
            details = data[0]["PostOffice"][0]
            address = {
                "state": details["State"],
                "district": details["District"],
                "city": details["Block"],
                "country": details["Country"],
                "postal_code": details["Pincode"],
            }
            return address
        else:
            return None

    def get(self, request):
        postal_code = request.query_params.get("postal_code")

        address_details = self.get_address_details(postal_code)
        if address_details:

            return Response(address_details)
        else:
            return Response(
                {"message": "Invalid PIN code or address not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )


from homepageapi.utils import create_voucher_data


class VoucherList(APIView):
    def add_field(self, dict_data):
        dict_data["order_date"] = self.order_date
        return dict_data

    def get(self, request):
        user = request.user
        try:
            order = Order.objects.filter(user=user)
            all_voucher_list = []
            for single_order in order:
                self.order_date = single_order.date_placed
                (
                    voucher_list,
                    i,
                    j,
                    basic_amount_radeemable,
                    total_tax,
                    total_discount,
                    balance_payable,
                    total_shipping_charge,
                ) = create_voucher_data(single_order.basket)
                if len(voucher_list) > 0:
                    voucher_list = list(map(self.add_field, voucher_list))

                all_voucher_list.extend(voucher_list)
        except Exception as e:
            logger.debug(e)
            import traceback

            f = traceback.format_exc()
            logger.debug(f"error in voucher{f=}")

            return Response(
                {"detail": "first login or you don't have any orders yet"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(all_voucher_list, status=status.HTTP_200_OK)


from apps.basket.models import Line
from apps.catalogue.models import ProductImage


class SingleOrderApi(APIView):
    serializer_class = BasketSerializer

    def get(self, request, number):
        
        order_object = Order.objects.get(number=number)
        total_price_exclusive_tax = 0.0
        total_gst_tax = 0.0

        basket = order_object.basket
        gift_excl = False

        cart_data = {}

        cart_data["order_total_amount"] = order_object.total_incl_tax
        cart_data["order_status"] = order_object.status
        cart_data["payment_mode"] = order_object.payment_types
        cart_data["shipping_address"] = ShipAddressSerializer(
            order_object.shipping_address, context={"request": request}
        ).data
        logger.debug(order_object.billing_address)
        try:
            cart_data["billing_address"] = BillAddressSerializer(
                order_object.billing_address, context={"request": request}
            ).data
        except Exception as e:
            pass
        cart_data["order_date"] = order_object.date_placed
        cart_data["shiping_charge"] = order_object.shipping_incl_tax

        try:
            (
                voucher_data_list,
                tota_offer_amount_after_voucher_calculation,
                total_payable,
                basic_amount_radeemable,
                total_tax,
                total_discount,
                balance_payable,
                shiping_charge_in_voucher,
            ) = create_voucher_data(basket)
        except Exception as e:
            tota_offer_amount_after_voucher_calculation = 0
            total_payable = 0
            voucher_data_list = str(e)
            shiping_charge_in_voucher = 0

        arrayProd = []
        total_product_value = 0
        total_tax2 = 0
        basic_amount_radeemable2 = 0
        total_amount_allocation = 0
        obj = Line.objects.filter(basket__id=basket.id).values(
            "id",
            "product",
            "product__title",
            "price_currency",
            "price_excl_tax",
            "price_incl_tax",
            "quantity",
        )
        for data in obj:

            lines = order_object.lines.filter(product__id=data["product"])
            log_idsp = lines[0].id
            logger.debug(f"{log_idsp}")
            sh = ShippingEventQuantity.objects.filter(
                line=lines[0], event__event_type__name="AWB Generated"
            )
            # new_status_change.lines.add(*lines_in_the_order)
            logger.debug(f"{sh=}")
            if sh.exists():
                awb = sh[0].event.notes

            else:
                awb = None

            dynData = data

            product_id = data["product"]
            objec = ProductImage.objects.filter(product=product_id).values("original")

            base_price = StockRecord.objects.filter(product=product_id).first()
            dynData["base_price"] = base_price.base_price
            dynData["awb"] = awb

            gst_tax_amount = data["price_excl_tax"] - dynData["base_price"]
            gst_tax_amount = gst_tax_amount * data["quantity"]
            total_price_exclusive_tax = float(total_price_exclusive_tax) + float(
                dynData["base_price"] * data["quantity"]
            )
            total_gst_tax = float(total_gst_tax) + float(gst_tax_amount)

            # add tax related logics.
            base_price = StockRecord.objects.filter(product=product_id).first()
            gst_tax_amount = base_price.calculate_gst_value()

            product_price = base_price.price
            dynData["mrp"] = base_price.mrp
            dynData["discount_type"] = base_price.discount_type
            dynData["discount"] = base_price.discount
            try:
                dynData["gst_rate"] = base_price.gst_rate.gst_rate.rate
            except:
                dynData["gst_rate"] = 0.0

            gst_total_tax_amount = round(gst_tax_amount, 2) * data["quantity"]

            total_gst_tax = float(total_gst_tax) + float(gst_total_tax_amount)
            dynData["gst_tax_amount"] = round(
                float(base_price.calculate_gst_value()), 2
            )
            dynData["base_price"] = round(float(base_price.get_base_price()), 2)
            dynData["image"] = objec
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
                dynData["gst_tax_amount"] = tax_amount
                dynData["base_price"] = taxable_amount
                dynData["price_excl_tax"] = base_price.price
                total_product_value = total_product_value + (
                    product_price * data["quantity"]
                )
                total_tax2 = total_tax2 + (tax_amount * data["quantity"])
                logger.debug(f"logging tax{total_tax2=} {tax_amount}")
                basic_amount_radeemable2 = basic_amount_radeemable2 + (
                    taxable_amount * data["quantity"]
                )
                dynData["amount_allocation_by_line"] = amount_allocation_by_line

                total_amount_allocation = (
                    total_amount_allocation + amount_allocation_by_line
                )

                gift_excl = True
                logger.debug(
                    f"{tax_amount=} {taxable_amount=} {product_price=} {total_product_value=} {total_tax2=} "
                )

            except:
                import traceback

                f = traceback.format_exc()
                logger.error(f"error in exclusive cacl in check out{f=}")
            arrayProd.append(dynData)

        cart_data["product_deatils"] = arrayProd

        cart_data["voucher_list"] = voucher_data_list
        cart_data["order_voucher_total_amount"] = round(
            tota_offer_amount_after_voucher_calculation
        )

        # cart_data['total_gst_payable'] = total_payable
        cart_data["total_product_gst_value"] = round(total_tax)
        cart_data["balance_payable"] = round(balance_payable)
        cart_data["basic_amount_radeemable"] = round(basic_amount_radeemable)
        try:
            cart_data["wallet_amount"] = order_object.wallet.wallet_used_amount
        except:
            pass

        try:
            cart_data["credit"] = CreditHistory.objects.get(
                order=order_object
            ).credit_used_amount
        except Exception as e:
            import traceback

            f = traceback.format_exc()
            logger.debug(f"error in history credit{f=}")

        cart_data["total_amount_allocation"] = round(total_amount_allocation, 0)

        if gift_excl == True:
            cart_data["basic_amount_radeemable"] = round(basic_amount_radeemable2)
            cart_data["total_product_gst_value"] = round(total_tax2)
            cart_data["balance_payable"] = round(total_product_value)

        return Response(cart_data)


class CheckOrder(APIView):
    def get(self, request):
        baskets = operations.get_basket(request)
        if baskets.vouchers.all().exists():
            return Response({"detail": "ready to checkout"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "can't checkout"}, status=status.HTTP_401_UNAUTHORIZED
            )


class FreezeStock(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            sender = settings.EMAIL_HOST_USER
            send_mail("freeze", "freeze api called", sender, ["pranavpranab@gmail.com"])
        except:
            pass
        baskets = operations.get_basket(request)
        logger.debug(request.user)
        logger.debug(baskets)
        freeze_id_list = []
        try:
            for i in baskets.lines.all():
                if (
                    i.product.stockrecords.all()[0].num_in_stock
                    - i.product.stockrecords.all()[0].num_allocated
                    >= i.quantity
                ):
                    i.product.stockrecords.all()[0].allocate(i.quantity)
                    freeze = Freeze.objects.create(
                        cart=baskets,
                        stock=i.product.stockrecords.all()[0],
                        quantity=i.quantity,
                    )
                    freeze_id_list.append(freeze.id)

            return Response(
                {"status": "freezed stock", "freeze_ids": freeze_id_list},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error("error in calling freeze api:",exc_info=True)
            import traceback
            f = traceback.format_exc()
            sender = settings.EMAIL_HOST_USER
            send_mail("freeze error", str(f), sender, ["pranavpranab@gmail.com"])

from django.db import transaction


class UnfreezeStock(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        sender = settings.EMAIL_HOST_USER

        freeze_id_list = request.data.get("freeze_id_list")
        try:
            send_mail("freeze", str(freeze_id_list), sender, ["pranavpranab@gmail.com"])
        except Exception as e :
            import traceback;
            f = traceback.format_exc()
            logger.error("error in sending email in freeze",exc_info=True)
            try:
                send_mail("unfreeze error", str(f), sender, ["pranavpranab@gmail.com"])

            except:
                pass
            
        logger.debug(freeze_id_list)
        baskets = operations.get_basket(request)

        for i in baskets.lines.all():
            logger.debug("inside for loop")
            try:
                fre = Freeze.objects.get(
                    cart=baskets,
                    id__in=freeze_id_list,
                    stock=i.product.stockrecords.all()[0],
                )
                i.product.stockrecords.all()[0].cancel_allocation(fre.quantity)
                fre.delete()
            except Exception as e:
                import traceback

                f = traceback.format_exc()
                sender = settings.EMAIL_HOST_USER

                send_mail(
                    "task runner failed for freeze",
                    str(f),
                    sender,
                    ["pranavpranab@gmail.com"],
                )

        return Response({"status": "rolled back"}, status=status.HTTP_200_OK)
