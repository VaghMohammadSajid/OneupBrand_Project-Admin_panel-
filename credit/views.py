from django.shortcuts import render
from .models import (
    Credit,
    grand_total_added_to_client,
    grand_total_amount_radeemed_by_cliend,
    CreditHistory,
    OtpForCredit,
)
from oneup_project.settings import ERP_URL,ERP_TOKEN
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from oscar.core.loading import get_model
from oscarapi.basket import operations
import logging
from useraccount.models import UniqueStrings
from django.views import View
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
import requests
from django.core.mail import send_mail, EmailMultiAlternatives
import csv
from django.http import HttpResponse
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from useraccount.models import ClientDetails
from useraccount.sms import SmsOtpIntegration
from random import randint
from homepageapi.models import CreditAmountUser

Cart = get_model("basket", "Basket")

logger = logging.getLogger(__name__)


# Create your views here.
def admin_view(request):
    wallet = Credit.objects.all()

    grand_total_added = grand_total_added_to_client().get("total_amount")
    grand_total_deducted = grand_total_amount_radeemed_by_cliend().get("total_amount")
    return render(
        request,
        "wallet/wallet_list.html",
        {
            "wallet": wallet,
            "grand_total_added": grand_total_added,
            "grand_total_deducted": grand_total_deducted,
            "page_data": "Credit",
            "redirect_string": "credit",
        },
    )


class TotalAmountApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            credit = Credit.objects.get(user=user)
            baskets = operations.get_basket(request)
            total_tax = 0
            for i in baskets.lines.all():
                total_tax = (
                    int(total_tax + i.stockrecord.calculate_gst_value()) * i.quantity
                )

            shipping_value = credit.credit_shipping_type

            if credit.credit_gst == "Inclusive":
                return Response(
                    {
                        "amount": credit.amount,
                        "minus_amount": 0,
                        "shipping_value": shipping_value,
                        "GST":True
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {
                        "amount": credit.amount,
                        "minus_amount": total_tax,
                        "shipping_value": shipping_value,
                        "GST":False
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            logger.error(e)
            return Response(
                {"error": "credit not found for this user"}, status=status.HTTP_200_OK
            )


class RemoveAmount(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        basket = operations.get_basket(request)
        amount = request.data.get("amount")

        credit_obj = Credit.objects.get(user=user)
        if credit_obj.remove_amount(int(amount), basket):
            return Response({"succes": "amount removed"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "not enough ammount"}, status=status.HTTP_400_BAD_REQUEST
            )


def credit_history(request, id):
    credit = Credit.objects.get(id=id)

    all_history = credit.history.all()
    radeemed_total = credit.remove_none(credit.total_amount_radeemed)
    added_total = credit.remove_none(credit.total_amount_added)
    logger.debug(f"{radeemed_total} {added_total} {all_history}")
    for i in all_history:
        logger.debug(i.__dict__)

    return render(
        request,
        "wallet/wallet_history.html",
        {
            "history": all_history,
            "radeemed_total": radeemed_total,
            "added_total": added_total,
            "page_data": "Credit",
        },
    )


# {'date': '01-07-2024', 'order_no': None, 'customer': 'Jishnu', 'credit_amount': 2000.0, 'debit_amount': 0.0, 'balance_amount': 2000.0, 'gst': 'Inclusive', 'shipping_charge': 'Yes'}

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


class CreditFlow(APIView):
    def post(self, request):
        logger.debug(f"credit request {request.data=}")
        data = request.data
        date = data.get("date")
        order_no = data.get("order_no")
        customer = data.get("customer")
        customer_id = data.get("customer_id")

        credit_amount = data.get("credit_amount")
        debit_amount = data.get("debit_amount")
        balance_amount = data.get("balance_amount")
        gst = data.get("gst")
        shipping_charge = data.get("shipping_charge")

        credit_request_id = data.get("credit_request_id")
        statusnew = data.get("status")
        reason = data.get("reason")
        logger.debug(f"{credit_request_id=} {statusnew=} {reason=} {credit_amount}")
        logger.debug(f"{request.data}")

        try:
            sender = settings.MAIL_HOST_INFO
            s = str(request.data)
            send_mail(
                "Credit Flow details", s, sender, ["akashsurendran1602@gmail.com"]
            )
        except Exception as e:
            sender = settings.MAIL_HOST_INFO

            error_message = f"Error processing rejected status: {str(e)}"
            logger.error(error_message)
            send_mail(
                "Credit Flow details",
                error_message,
                sender,
                ["akashsurendran1602@gmail.com"],
            )
            return Response(
                {"message": "Error processing rejected status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            user = UniqueStrings.objects.get(unique_string=customer_id).user

        except:
            return Response(
                {"message": "Credit request not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        credit_obj = Credit.objects.get(user=user)
       
        if statusnew == "Credit Transferred":

            try:
                credit_request = CreditRequestUser.objects.get(
                    credit_request_id=credit_request_id
                )
                credit_request.status = statusnew
                credit_request.save()

                credit_obj.add_amount(
                    add_amount=credit_amount, credit_req=credit_request
                )
                credit_obj.credit_gst = gst
                credit_obj.credit_shipping_type = shipping_charge == "Inclusive"
                credit_obj.save()

                return Response({"success": True}, status=status.HTTP_201_CREATED)

            except CreditRequestUser.DoesNotExist:
                logger.error("error in saving credit 2", exc_info=True)
                return Response(
                    {"message": "Credit request not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        elif statusnew == "Cancelled":
            try:
                credit_request = CreditRequestUser.objects.get(
                    credit_request_id=credit_request_id
                )
                credit_request.status = statusnew
                credit_request.reason = reason
                credit_request.save()

                return Response({"success": True}, status=status.HTTP_200_OK)
            except CreditRequestUser.DoesNotExist:
                return Response(
                    {"message": "Credit request not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        else:
            try:
                credit_request = CreditRequestUser.objects.get(
                    credit_request_id=credit_request_id
                )
                credit_request.status = statusnew
                credit_request.reason = reason
                credit_request.save()

                return Response({"success": True}, status=status.HTTP_200_OK)
            except CreditRequestUser.DoesNotExist:
                return Response(
                    {"message": "Credit request not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            # return Response({"message": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)


class CreditAvailableAmount(APIView):
    def post(self, request):
        user = request.user


from .models import CreditRequestUser
from .serializers import CreditRequestUserSerializer


class CreditRequestUserApi(APIView):
    def get(self, request, pk):

        try:
            credit_data = CreditRequestUser.objects.filter(user=pk).order_by(
                "-submission_date"
            )
            serializer = CreditRequestUserSerializer(credit_data, many=True)
            return Response({"Credit Request Data": serializer.data})
        except CreditRequestUser.DoesNotExist:
            return Response({"error": "Credit request user not found."}, status=404)

    def post(self, request, *args, **kwargs):
        request_data = request.data.copy()

        serializer = CreditRequestUserSerializer(data=request_data)
        if serializer.is_valid():
            credit_request_user = serializer.save()

            # Send data to ERP system using a separate function
            try:
                response = self.send_data_to_erp(credit_request_user)
            except requests.exceptions.RequestException as e:
                sender = settings.MAIL_HOST_INFO

                error_message = f"Error processing rejected status: {str(e)}"
                logger.error(error_message)
                send_mail(
                    "Credit Flow details reqest time front end",
                    error_message,
                    sender,
                    ["akashsurendran1602@gmail.com"],
                )
                return Response(
                    {"message": "Error processing rejected status"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def send_data_to_erp(self, credit_request_user):
        erp_url = f"{ERP_URL}api/method/django_ecommerce.api.credit_request"
        HEADERS = {
            "Authorization": f"token {ERP_TOKEN}",
            "Content-Type": "application/json",
        }
        userid = UniqueStrings.objects.get(user__id=credit_request_user.user.id)
        erp_data = {
            "credit_request_id": credit_request_user.credit_request_id,
            "user_id": userid.unique_string,
            "amount": float(credit_request_user.amount),
            "submission_date": credit_request_user.submission_date.isoformat(),
            "status": credit_request_user.status,
        }
        try:
            erp_response = requests.post(url=erp_url, headers=HEADERS, json=erp_data)
            s = str(erp_response.__dict__)
            s = s + str(userid.unique_string)
            sender = settings.MAIL_HOST_INFO
            send_mail(
                "Credit Flow details reqest time front end",
                s,
                sender,
                ["akashsurendran1602@gmail.com"],
            )

            return Response({"succes": True}, status=status.HTTP_200_OK)

        except Exception as e:
            sender = settings.MAIL_HOST_INFO
            send_mail(
                "Credit Flow details reqest time front end",
                str(e),
                sender,
                ["akashsurendran1602@gmail.com"],
            )
            return {"status": "error", "details": str(e)}


class CreditRequestUserList(View):
    template_name = "credit/CreditList.html"

    def get(self, request):
        credit_requests_data = CreditRequestUser.objects.all().order_by(
            "-submission_date"
        )
        return render(
            request, self.template_name, {"credit_requests_data": credit_requests_data}
        )


class CreditRequestUserDelete(View):
    def get(self, request, pk):
        credit_request = get_object_or_404(CreditRequestUser, pk=pk)
        credit_request.delete()
        return redirect(reverse("credit-request-user-list"))


from .serializers import CreditSerializer


class CreditHistoryApiView(APIView):
    def get(self, request):
        try:
            user = request.user

            credit = Credit.objects.get(user=user)

            serializer = CreditSerializer(credit)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Credit.DoesNotExist:
            return Response(
                {"error": "Credit not found"}, status=status.HTTP_404_NOT_FOUND
            )


class CreditRequestErp(APIView):
    def post(self, request, *args, **kwargs):
        try:
            request_data = request.data.copy()

            # Extract user_id from the incoming data
            customer_id = request_data.get("user_id")
            if not customer_id:
                return Response(
                    {"message": "user_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Find the user based on the customer_id
            unique_string_obj = get_object_or_404(
                UniqueStrings, unique_string=customer_id
            )
            user = unique_string_obj.user

            # Extract other fields from the incoming data
            amount = request_data.get("amount")
            statusnew = request_data.get("status")
            reason = request_data.get("reason", "")

            # Create a new CreditRequestUser instance
            credit_request = CreditRequestUser.objects.create(
                user=user, amount=amount, status=statusnew, reason=reason, erp=True
            )

            return Response(
                {"credit_request_id": credit_request.credit_request_id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            # Send error details via email
            sender = settings.MAIL_HOST_INFO
            send_mail("Credit Flow Error", str(e), sender, ["pranavpranab@gmail.com"])

            return Response(
                {"message": "An error occurred", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from oscarapi.basket import operations


class CreditHistoryDowloadView(APIView):
    def get(self, request):
        try:
            user = request.user
            credit = Credit.objects.get(user=user)
            start_date = request.query_params.get("start_date", None)
            end_date = request.query_params.get("end_date", None)
            days = request.query_params.get("days", None)
            month = request.query_params.get("month", None)
            year = request.query_params.get("year", None)

            if start_date and end_date:
                start_date = timezone.make_aware(
                    datetime.strptime(start_date, "%Y-%m-%d")
                )
                end_date = (
                    timezone.make_aware(datetime.strptime(end_date, "%Y-%m-%d"))
                    + timedelta(days=1)
                    - timedelta(seconds=1)
                )
                credit_history = CreditHistory.objects.filter(
                    credit_id=credit.id,
                    credit_used_time__lte=end_date,
                    credit_used_time__gte=start_date,
                )

            else:
                credit_history = CreditHistory.objects.filter(credit_id=credit.id)

            if not credit_history.exists():
                return Response(
                    {"error": "Credit history not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="credit_history_{credit.id}.csv"'
            )

            writer = csv.writer(response)
            writer.writerow(
                [
                    "Credit ID",
                    "Credit Used Amount",
                    "Credit Used Time",
                    "Order ID",
                    "Request ID",
                ]
            )

            for history in credit_history:
                writer.writerow(
                    [
                        history.credit.id,
                        history.credit_used_amount,
                        history.credit_used_time,
                        history.order.number if history.order else "",
                        (
                            history.credit_request.credit_request_id
                            if history.credit_request
                            else ""
                        ),
                    ]
                )

            return response
        except Exception as e:
            logger.error("error in generating csv for credit history", exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def calculate_days(days=None, month=None, year=None):
    if days:
        end_date = date.today()
        starting_date = end_date - timedelta(days=days)
        return starting_date, end_date
    elif month:
        end_date = date.today()
        starting_date = (end_date - relativedelta(months=3)).replace(day=1)
        return starting_date, end_date
    elif year:
        end_date = date.today()
        starting_date = (end_date - relativedelta(year=year - 1)).replace(
            month=1, day=1
        )
        return starting_date, end_date
    else:
        return None, None





class CreditotpApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            client = ClientDetails.objects.get(user=user)
        except:
            return Response(
                {"message": "user doesn't exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        mobile_no = client.mobile_no
        otp = randint(100000, 999999)
        try:
            otp_ob = OtpForCredit.objects.get(user=user)
        except Exception as e:
            logger.error("error in getting otp",exc_info=True)
            otp_ob = OtpForCredit.objects.create(user=user, otp=otp)

        otp_ob.otp = otp
        otp_ob.save()
        SmsOtpIntegration.send_otp_for_credit_verification(
            otp=otp, mobile_no=mobile_no, username=None, amount=None
        )
        return Response({"message": "otp send"}, status=status.HTTP_200_OK)


class CreditotpVerifyApi(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        otp = request.data.get("otp")
        try:
            otp_ob = OtpForCredit.objects.get(user=user)
        except Exception as e:
            return Response(
                {"message": "client not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if otp_ob.otp == otp:
            return Response({"message": "phone verified"}, status=status.HTTP_200_OK)
        return Response(
            {"message": "incorrect otp"}, status=status.HTTP_400_BAD_REQUEST
        )
from decimal import Decimal, InvalidOperation
class CreditApplyCart(APIView):
    def post(self,request):
        shipping_charge = request.data.get("shipping_charge")
        cart = operations.get_basket(request)
        credit = Credit.objects.get(user=request.user)
        shipping_charge_bool = credit.credit_shipping_type
        credit_gst = credit.credit_gst
        
        total_price = 0
        total_tax = 0
        for single_line in cart.lines.all():
            logger.debug(single_line)
            total_price = total_price + (single_line.stockrecord.price * single_line.quantity)
            total_tax = total_tax + single_line.stockrecord.gst_value
        if shipping_charge_bool:
            try:
                total_price = total_price + Decimal(shipping_charge) 
            except InvalidOperation:
                return Response({"msg":"enter a valid shipping charge"},status=status.HTTP_400_BAD_REQUEST)
        if credit_gst == "Exclusive":
            total_price = total_price - total_tax
        if not (credit.amount > total_price):
            total_price = credit.amount
        try:
            credit_cart = CreditAmountUser.objects.get(user=request.user,cart=cart)
            credit_cart.amount = total_price
            credit_cart.save()
        except CreditAmountUser.DoesNotExist:
            credit_cart = CreditAmountUser.objects.create(user=request.user,cart=cart,amount=total_price)
        except Exception as e:
            return Response({"msg":"credit added failed"},status=status.HTTP_400_BAD_REQUEST)

        return Response({"msg":"credit added succesfully"},status=status.HTTP_201_CREATED)
    

class CartRemoveCredit(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        cart = operations.get_basket(request)
        try:
            CreditAmountUser.objects.get(user=request.user,cart=cart).delete()
        except:
            return Response({"msg":"No credit found"},status=status.HTTP_400_BAD_REQUEST)
        return Response({"msg":"Credit removed"},status=status.HTTP_200_OK)