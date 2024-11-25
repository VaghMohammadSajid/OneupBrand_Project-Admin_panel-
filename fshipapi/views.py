from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from oscar.core.loading import get_model
from rest_framework.response import Response

import requests as r
from oscarapi.basket import operations
from oneup_project.settings import FSIP_API_SIGNATURE, RATE_CALCULATOR_URL
from rest_framework import status
from apps.basket.models import ShippinCharge
import logging

stock = get_model("partner", "StockRecord")
address = get_model("address", "UserAddress")

logger = logging.getLogger(__name__)


class CheckAdd(APIView):
    def get(self, request):
        try:
            add = address.objects.filter(user=request.user)
        except:
            return Response({"detail": "error"}, status=status.HTTP_400_BAD_REQUEST)
        if add.exists():
            pin = add.first().postcode
            return Response({"PIN": "pin"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "address not found"}, status=status.HTTP_404_NOT_FOUND
            )


import requests
import json


def shiprocket_login():
    url = "https://apiv2.shiprocket.in/v1/external/auth/login"
    email = "akashak1602@gmail.com"
    password = "Oneup@123"

    payload = json.dumps({"email": email, "password": password})

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get("token", None)
            return access_token
        else:
            logger.debug(f"Failed to authenticate. Status code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logger.debug(f"Error occurred: {e}")
        return None


class ShipAvailableAPi(APIView):
    def post(self, request):
        pin = request.data.get("pin_code")
        access_token = shiprocket_login()

        if access_token:

            url = "https://apiv2.shiprocket.in/v1/external/courier/serviceability/"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }

            payload = {
                "pickup_postcode": "110030",
                "delivery_postcode": pin,
                "weight": 1.5,
                "cod": 1,
            }

            response = requests.get(url, headers=headers, params=payload)

            if response.status_code == 200:
                data = response.json()
                available_courier_companies = data.get("data", {}).get(
                    "available_courier_companies", []
                )

                if available_courier_companies:
                    # Delivery is available
                    return Response(
                        {"data": "delvery available"}, status=status.HTTP_200_OK
                    )
                else:
                    # No delivery options found
                    return Response(
                        {"data": "Delivery not available"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            else:
                logger.error(
                    f"API request failed with status code: {response.status_code}"
                )
                return Response(
                    {"data": "API request failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        else:
            logger.error("Access token not available")
            return Response(
                {"data": "Access token not available"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class RateCalcOnPdpPageAPi(APIView):
    def get(self, request):
        pin = request.query_params.get("pin")
        product_id = request.query_params.get("id")
        quantity = request.query_params.get("quantity")
        stock_details = stock.objects.get(product__id=product_id)

        access_token = shiprocket_login()

        if access_token:

            url = "https://apiv2.shiprocket.in/v1/external/courier/serviceability/"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }

            payload = {
                "pickup_postcode": "110030",
                "delivery_postcode": pin,
                "weight": float(stock_details.weight) * float(quantity),
                "cod": 1,
                "length": float(stock_details.length) * float(quantity),
                "breadth": float(stock_details.breadth),
                "height": float(stock_details.height),
            }

            response = requests.get(url, headers=headers, params=payload)

            if response.status_code == 200:
                data = response.json()
                available_courier_companies = data.get("data", {}).get(
                    "available_courier_companies", []
                )

                min_rate = float("inf")
                min_delivery_days = float("inf")
                selected_courier = None

                for courier in available_courier_companies:
                    rate = courier.get("rate", float("inf"))
                    delivery_days = int(
                        courier.get("estimated_delivery_days", float("inf"))
                    )

                    if rate < min_rate or (
                        rate == min_rate and delivery_days < min_delivery_days
                    ):
                        # Update the minimum rate and choose the one with lesser delivery days if rates are same
                        min_rate = rate
                        min_delivery_days = delivery_days
                        selected_courier = courier

                if selected_courier:
                    # Return the minimum rate rounded to 2 decimal places
                    return Response(
                        {"rate": round(min_rate, 0)}, status=status.HTTP_200_OK
                    )

                else:
                    return Response({"rate": None}, status=status.HTTP_404_NOT_FOUND)

            else:
                logger.error(
                    f"API request failed with status code: {response.status_code}"
                )
                return Response(
                    {"rate": None}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        else:
            logger.error("Access token not available")
            return Response({"rate": None}, status=status.HTTP_401_UNAUTHORIZED)


class ShipPriceCalcAPI(APIView):
    def post(self, request):
        pin = request.data.get("pin_code", None)
        print(request.user)
        print(request.headers)
        try:
            basket = operations.get_basket(request)
            total_weight = 0
            total_length = 0
            total_height = 0
            total_breadth = 0
            for single_line in basket.lines.all():

                total_weight = total_weight + (
                    single_line.stockrecord.weight * single_line.quantity
                )
                if total_length < single_line.stockrecord.length:
                    total_length = single_line.stockrecord.length
                if total_breadth < single_line.stockrecord.breadth:
                    total_breadth = single_line.stockrecord.breadth
                total_height = total_height + (
                    single_line.stockrecord.height * single_line.quantity
                )

        except Exception as e:
            return Response("no products in basket", status=status.HTTP_400_BAD_REQUEST)

        logger.debug(f"{total_weight=}")
        logger.debug(f"{total_length=}")
        logger.debug(f"{total_height=}")
        logger.debug(f"{total_breadth=}")

        if (
            total_height < 0
            or total_length < 0
            or total_weight < 0
            or total_breadth < 0
        ):
            return Response("no products in basket", status=status.HTTP_400_BAD_REQUEST)
        if pin == None:
            add = address.objects.filter(user=request.user)
            if add.exists():
                pin = add.first().postcode
            else:
                return Response(
                    {"detail": "address not found"}, status=status.HTTP_404_NOT_FOUND
                )

        access_token = shiprocket_login()

        if access_token:

            url = "https://apiv2.shiprocket.in/v1/external/courier/serviceability/"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }

            payload = {
                "pickup_postcode": "110030",
                "delivery_postcode": f"{pin}",
                "weight": float(total_weight),
                "cod": 1,
                "length": float(total_length),
                "breadth": float(total_breadth),
                "height": float(total_height),
            }

            response = requests.get(url, headers=headers, params=payload)

            # if response.status == 400 :
            logger.debug(f"{response.json()=}")
            if response.json().get("status") == 404:
                return Response(
                    " No Courier serviceable for entered pincodes ",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if response.status_code == 200:
                data = response.json()
                available_courier_companies = data.get("data", {}).get(
                    "available_courier_companies", []
                )

                min_rate = float("inf")
                min_delivery_days = float("inf")
                selected_courier = None

                for courier in available_courier_companies:
                    rate = courier.get("rate", float("inf"))
                    delivery_days = int(
                        courier.get("estimated_delivery_days", float("inf"))
                    )

                    if rate < min_rate or (
                        rate == min_rate and delivery_days < min_delivery_days
                    ):
                        # Update the minimum rate and choose the one with lesser delivery days if rates are same
                        min_rate = rate
                        min_delivery_days = delivery_days
                        selected_courier = courier

                if selected_courier:
                    courier_name = selected_courier.get("courier_name", None)
                    rate = round(min_rate, 0)
                    courier_id = selected_courier.get("courier_company_id", None)

                    try:
                        shipping_charge = ShippinCharge.objects.get(basket_id=basket.id)
                    except ShippinCharge.DoesNotExist:
                        shipping_charge = ShippinCharge(basket_id=basket.id)
                    except:
                        return Response(
                            " courier Service not avilabile ",
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    shipping_charge.charge = round(min_rate, 0)
                    shipping_charge.courier_id = courier_id
                    shipping_charge.courier_name = courier_name
                    shipping_charge.save()

                    response_payload = {
                        "shipping_courier_name": courier_name,
                        "total_rate": rate,
                    }

                    # Return the response with the custom fields
                    return Response(response_payload, status=status.HTTP_200_OK)

                else:
                    return Response(
                        " courier Service not avilabile ",
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            else:
                logger.error(
                    f"API request failed with status code: {response.status_code}"
                )
                return Response(
                    " courier Service not avilabile ",
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            logger.error("Access token not available")
            return Response(
                " courier Service not avilabile ", status=status.HTTP_400_BAD_REQUEST
            )


class OrderTrackNow(APIView):
    def get(self, request):
        awb = request.query_params.get("awb")
        token = shiprocket_login()

        url = f"https://apiv2.shiprocket.in/v1/external/courier/track/awb/{awb}"

        payload = {}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        logger.debug(response.__dict__)
        res = response.json()
        logger.debug(response.status_code)
        logger.debug(f"{res} wth shiprocketresponse")

        return Response(response.text)
