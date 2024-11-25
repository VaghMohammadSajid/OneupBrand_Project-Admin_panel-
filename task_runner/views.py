from django.shortcuts import render,HttpResponse
import logging
from oscar.core.loading import get_model
import requests
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from rest_framework.response import Response
from useraccount.models import UpdateErpstatus
from rest_framework.views import APIView
from rest_framework import status
from .task import long_running_task

# Create your views here.
logger = logging.getLogger(__name__)
from fshipapi.views import shiprocket_login
from oneup_project.settings import ERP_URL

ShippingEvent = get_model("order", "ShippingEvent")
ShippingEventQuantity = get_model("order", "ShippingEventQuantity")
ShippingEventType = get_model("order", "ShippingEventType")
Line = get_model("order", "Line")


Order = get_model("order", "Order")
"""https://apiv2.shiprocket.in/v1/external/courier/track/shipment/16104408"""


def Check_order_status():
    all_order = Order.objects.exclude(status="Delivered")

    access_token = shiprocket_login()
    for single_order in all_order:
        for single_line in single_order.lines.all():
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            
            if single_line.shipping_events.all().count() == 2:
    
                
                for single_line_status in single_line.shipping_events.all().filter(
                    event_type__name="AWB Generated"
                ):
                    awb_no = single_line_status.notes
                    response = requests.get(
                        url=f"https://apiv2.shiprocket.in/v1/external/courier/track/awb/{awb_no}",headers=headers
                    )
                    logger.info(response.__dict__)
                    import json
                    logger.info(json.dumps(response.json(), indent=4, sort_keys=True))
                    if response.status_code == 200:
                        logger.info("response 200")
                        logger.info(response.__dict__)
                        response_json = response.json()
                        if response_json["tracking_data"]["shipment_track_activities"] == None:
                            continue
                        if (
                            response_json["tracking_data"]["shipment_track_activities"][
                                0
                            ]["activity"]
                            == "Delivered"
                        ):
                            try:
                                shippingEventType = ShippingEventType.objects.create(
                                    name="Delivered"
                                )
                            except:
                                shippingEventType = ShippingEventType.objects.get(
                                    name="Delivered"
                                )
                            logger.debug(f"{shippingEventType=}")
                            new_status_change = ShippingEvent.objects.create(
                                order=single_order,
                                event_type=shippingEventType,
                                notes=awb_no,
                            )

                            logger.debug(f"{single_line.quantity=}")
                            new_event = ShippingEventQuantity.objects.create(
                                line=single_line,
                                event=new_status_change,
                                quantity=single_line.quantity,
                            )
                            logger.debug(f"{new_event=}")
                            new_status_change.lines.add(*single_line)
                        if (
                            response_json["tracking_data"]["shipment_track_activities"][
                                0
                            ]["activity"]
                            == "In Transit"
                        ):
                            try:
                                shippingEventType = ShippingEventType.objects.create(
                                    name="Shipped"
                                )
                            except:
                                shippingEventType = ShippingEventType.objects.get(
                                    name="Shipped"
                                )
                            logger.debug(f"{shippingEventType=}")
                            new_status_change = ShippingEvent.objects.create(
                                order=single_order,
                                event_type=shippingEventType,
                                notes=awb_no,
                            )

                            logger.debug(f"{single_line.quantity=}")
                            new_event = ShippingEventQuantity.objects.create(
                                line=single_line,
                                event=new_status_change,
                                quantity=single_line.quantity,
                            )
                            logger.debug(f"{new_event=}")
                            new_status_change.lines.add(*single_line)
        HEADERS = {
            "Authorization": "token b338acdcc391620:c1391947f4a80ab",
            "Content-Type": "application/json",
        }
        if (
            single_order.lines.all().count()
            == single_order.shipping_events.all()
            .filter(event_type__name="Shipped")
            .count()
        ):
            single_order.status = "Shipped"
            single_order.save()
        elif (
            single_order.shipping_events.all()
            .filter(event_type__name="Shipped")
            .count()
            > 0
        ):
            single_order.status = "Partially Shipped"
            single_order.save()
            
        if (
            single_order.lines.all().count()
            == single_order.shipping_events.all()
            .filter(event_type__name="Delivered")
            .count()
        ):
            single_order.status = "Delivered"
            order_data = {
                "order_no": single_order.number,
                "items": [{"item": i.product.upc} for i in single_order.lines.all()],
                "status": "Delivered",
            }
            requests.post(
                url=f"{ERP_URL}api/method/django_ecommerce.api.update_shipment_status",
                data=order_data,
                headers=HEADERS,
            )
            single_order.save()
        elif (
            single_order.shipping_events.all()
            .filter(event_type__name="Delivered")
            .count()
            > 0
        ):
            single_order.status = "Partially Delivered"
            order_data = {
                "order_no": single_order.number,
                "items": [{"item": i.product.upc} for i in single_order.lines.all()],
                "status": "Delivered",
            }
            requests.post(
                url=f"{ERP_URL}api/method/django_ecommerce.api.update_shipment_status",
                data=order_data,
                headers=HEADERS,
            )

            single_order.save()

    logger.debug(f"order status checked")


from cart_api.models import Freeze
from datetime import timedelta
from django.utils import timezone


def check_unfreeze():
    try:
        current_time_in_india = timezone.now()
        time_to_check = current_time_in_india - timedelta(minutes=5)
        for single_freeze in Freeze.objects.all():
            if single_freeze.created_date < time_to_check:
                single_freeze.stock.cancel_allocation(single_freeze.quantity)
                single_freeze.delete()
        logger.debug("deleted everything")
    except Exception as e:
        import traceback

        f = traceback.format_exc()
        sender = settings.EMAIL_HOST_USER
        send_mail(
            "task runner failed for freeze", str(f), sender, ["pranavpranab@gmail.com"]
        )


class SendStatus(APIView):
    def post(self, request):
        try:

            created_item_upc = UpdateErpstatus.objects.filter(
                update_erp=False
            ).values_list("upc", flat=True)
            long_running_task.delay(list(created_item_upc))
        except Exception as e:
            import traceback

            f = traceback.format_exc()
            logger.critical(f"error in sending data to erp for updating the status {f}")

        return Response(
            {"succes": True, "msg": "task running in the background"},
            status=status.HTTP_200_OK,
        )
from .task import task_testing

class TestCeleryAPi(APIView):
    def post(self,request):
        task_testing.delay()
        return Response({"succes":True},status=status.HTTP_200_OK)


import razorpay
from django.conf import settings
from django.http import JsonResponse
from apps.order.models import Razorpay
from django.utils import timezone
from datetime import timedelta
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET_KEY))
from django.db import connection

"""
need to check the query execution
"""
def fetch_payment_status():
    now = timezone.now() - timedelta(minutes=10)
    query_set =Razorpay.objects.filter(created_at__gte=now,raz_status='NOT_CHECKED').select_related('order_id')
    for Single_payment in query_set :
        try:
            payment = client.payment.fetch(Single_payment.payment_id)
            status = payment['status']
            if status == 'captured':
                Single_payment.raz_status = 'captured'
                Single_payment.save()
            else:
                logger.critical("Need to notify the admin about raz pay issue")
            if not (payment['amount'] == Single_payment.total_amount):
                logger.critical("There is a mismatch in total amount")
            
        except razorpay.errors.BadRequestError as e:
            logger.error("erorr bad request razor pay",exc_info=True)
        except Exception as e:
            logger.error("erorr Don't know",exc_info=True)
        
   