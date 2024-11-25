import re

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction, IntegrityError
from django.shortcuts import render
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode
from django.views import View
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.hashers import make_password
import requests
from openpyxl.workbook import Workbook
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from datetime import datetime, timedelta
from useraccount.serializers import (
    EmailSentSerializer,
    LoginSerializer,
    VarifyRegistrationSerializer,
    VoucherSerializer,
    PasswordEmailSerializer,
    VerifyOTPSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    VoucherUsertDetailsSerializer,
    ClientEmailVerifySerializer,
    SignupCheckingSerializer,
    GetHelpOnHomePageSerializer,
)
from .models import (
    UserAuthTokens,
    UserProfile,
    OTP,
    ClientEmailVerify,
    OnboardingGstVerify,
    # OnboardingAlternativePersonDetails,
    OnboardingBussinessDetails,
    OnboardingBankDetails,
    GetHelpOnHomePage,
    OnboardingCommunication,
    OnboardingRegisteredAddress,
    WarehouseAddress,
    OutletAddress

)
from pytz import timezone

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import (
    ClientDetails,
    VoucherUser,
    RequestBussinessRegister,
    ClientRequestDetails,
)
from .serializers import (
    ClientDetailsSerializer,
    OnboardingGstSerializer,
    OnboardingRegisterSerializer,
    OnboardingBussinessDetailsSerializer,
    OnboardingBankDetailsSerializer,
    # OnboardingAlternativePersonDetailsSerializer,
    OnboardingCommunictionSerializer,
    OnboardingregisterAddressSerializer,
    FullDataSerializer,
    OnboardingWarehouseAddressSerializer,
    OnboardingOutletAddresssSerializer
)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
import string
import secrets
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from role_permission.models import Roles, Permissions
from .models import VocherLoginConnect
from .utils import check_voucher_code
from oscar.core.loading import get_model
from django.db.models import Count
from django.core.paginator import Paginator
from .models import UniqueStrings
from .utils import send_client_data_to_user
from django.http import HttpResponse

Basket = get_model("basket", "Basket")

# from .models import VocherLoginConnect
# Create your views here.
order_model = get_model("order", "order")


class ClientUserListView(View):
    def get(self, request):
        # Assuming you have imported the necessary models
        client = ClientDetails.objects.all().values_list("id", flat=True)
        users = User.objects.filter(
            groups__name="client", client__in=client
        ).order_by(
            "-date_joined"
        )  # Change the ordering field as needed
        paginator = Paginator(users, 20)  # Show 10 users per page

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        users_with_client_details = []
        for user in page_obj:
            client_details = ClientDetails.objects.filter(user=user)
            client_details_data = []
            for client_detail in client_details:
                client_detail_data = {
                    "gst_no": client_detail.gst_no,
                    "mobile_no": client_detail.mobile_no,
                    "current_date": client_detail.user.date_joined,
                }
                client_details_data.append(client_detail_data)

            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "client_details": client_details_data,
            }
            users_with_client_details.append(user_data)

        context = {
            "users_with_client_details": users_with_client_details,
            "page_obj": page_obj,  # Pass the page object to the template
        }
        return render(request, "useraccount/client_list.html", context)


UserAddress = get_model("address", "UserAddress")
Country = get_model("address", "Country")


class ClientUser(View):
    def get(self, request):
        users_with_client_details = []

        users = User.objects.filter(groups__name="client")

        for user in users:
            client_details = ClientDetails.objects.filter(
                user__username=user.username
            ).values("gst_no", "mobile_no")
            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "client_details": [
                    {
                        "gst_no": client_detail["gst_no"],
                        "mobile_no": client_detail["mobile_no"],
                    }
                    for client_detail in client_details
                ],
            }
            users_with_client_details.append(user_data)

        context = {
            "users_with_client_details": users_with_client_details,
        }
        return render(request, "useraccount/user.html", context)

    def post(self, request):
        email = request.POST.get("email")
        primary_contact_person = request.POST.get("primary_contact_person")
        designation = request.POST.get("designation")
        mobile_no = request.POST.get("mobile_no")
        bussiness_name = request.POST.get("bussiness_name")

        email_error = ""
        if not email:
            email_error = "Email is required."
        elif not is_valid_email(email):
            email_error = "Please enter a valid email address."

        primary_contact_person_error = ""
        if not primary_contact_person:
            primary_contact_person_error = "Person Name is required."

        mobile_no_error = ""
        if not mobile_no:
            mobile_no_error = "Mobile Number is required."
        elif not is_valid_mobile_number(mobile_no):
            mobile_no_error = "Mobile Number must be a 10-digit number."

        designation_error = ""
        if not designation:
            designation_error = "Designation is required"

        bussiness_name_error = ""
        if not bussiness_name:
            bussiness_name_error = "Business name is required"

        if (
            email_error
            or mobile_no_error
            or primary_contact_person_error
            or designation_error
            or bussiness_name_error
        ):
            return render(
                request,
                "useraccount/user.html",
                {
                    "email_error": email_error,
                    "primary_contact_person_error": primary_contact_person_error,
                    "mobile_no_error": mobile_no_error,
                    "designation_error": designation_error,
                    "bussiness_name_error": bussiness_name_error,

                    "email": email,
                    "primary_contact_person": primary_contact_person,
                    "designation": designation,
                    "mobile_no": mobile_no,
                    "bussiness_name": bussiness_name,
                },
            )
        else:
            client_details = ClientDetails.objects.filter(
                user__groups__name="client", user__email=email, mobile_no=mobile_no
            )
            if not client_details:
                if email and mobile_no:
                    is_user_exists = RequestBussinessRegister.objects.filter(
                        email=email, mobile_number=mobile_no
                    ).exists()
                    if not is_user_exists:
                        user = RequestBussinessRegister.objects.create(
                            primary_contact_person=primary_contact_person,
                            email=email,
                            designation=designation,
                            mobile_number=mobile_no,
                            bussiness_name=bussiness_name,
                        )
                        messages.success(
                            request,
                            f"Client Verification and Register Successfully Completed. Please complete the Gst page and the rest of the process.",
                        )
                        return render(
                            request, "useraccount/user.html", {"client_id": user.pk}
                        )
                    else:
                        existing_user = RequestBussinessRegister.objects.get(
                            email=email, mobile_number=mobile_no
                        )
                        messages.error(
                            request,
                            f'"{email}" have already Verify and Register, Please complete the gst page and the rest of the process.',
                        )
                        return render(
                            request,
                            "useraccount/user.html",
                            {
                                "email_error": email_error,
                                "primary_contact_person_error": primary_contact_person_error,
                                "client_id": existing_user.pk,

                                "email": email,
                                "primary_contact_person": primary_contact_person,
                                "designation": designation,
                                "mobile_no": mobile_no,
                                "bussiness_name": bussiness_name,
                            },
                        )
                else:
                    messages.error(self.request, "Something Went Wrong.")
                    return redirect("client-list")
            else:
                messages.error(self.request, "Already Client Registered: " + email)
                return redirect("client-list")


class ClientOnboardingStepOne(View):
    def post(self, request):
        request_user = self.request.POST.get("request_user")
        gst_no = self.request.POST.get("gst_no")
        pancard_no = self.request.POST.get("pancard_no")
        date_of_establishment = self.request.POST.get("date_of_establishment")

        date_of_establishment_error = ""
        if not date_of_establishment:
            date_of_establishment_error = "Date is required"

        if any([date_of_establishment_error]
        ):
            return render(
                request,
                "useraccount/user.html",
                {
                    # 'pancard_number_error': pancard_number_error,
                    "date_of_establishment_error": date_of_establishment_error,
                    "client_id": request_user,
                    "gst_no": gst_no,
                    "date_of_establishment": date_of_establishment,
                },
            )
        else:
            if request_user:
                bussiness_data = RequestBussinessRegister.objects.get(pk=request_user)
                gst_user = OnboardingGstVerify.objects.filter(
                    request_user=bussiness_data
                ).exists()
                if not gst_user:
                    gst_number_exist = OnboardingGstVerify.objects.filter(
                        gst_number=gst_no
                    )
                    if not gst_number_exist:
                        gst_data = OnboardingGstVerify(
                            request_user=bussiness_data,
                            gst_number=gst_no,
                            date_of_establishment=date_of_establishment,
                            pancard_no=pancard_no,
                        )
                        gst_data.save()
                        messages.success(
                            request,
                            "Gst Verification Successfully Completed. Please complete the Bussiness page and the rest of the process.",
                        )
                        return render(
                            request,
                            "useraccount/user.html",
                            {
                                "client_id": bussiness_data.pk,
                                "onboarding_gst_verify": gst_data.pk,
                            },
                        )
                    else:
                        messages.error(request, "Gst Already exists.")
                        return render(
                            request,
                            "useraccount/user.html",
                            {
                                # 'pancard_number_error': pancard_number_error,
                                "date_of_establishment_error": date_of_establishment_error,

                                "client_id": request_user,
                                "onboarding_gst_verify": gst_number_exist.pk,

                                "gst_no": gst_no,
                                "pancard_no": pancard_no,
                                "date_of_establishment": date_of_establishment,
                            },
                        )

                else:
                    existing_gst = OnboardingGstVerify.objects.get(
                        request_user=bussiness_data
                    )
                    messages.error(
                        request,
                        f'"{gst_no}" have already gst verification, Please complete the Bussiness page and the rest of the process.',
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            # 'pancard_number_error': pancard_number_error,

                            "date_of_establishment_error": date_of_establishment_error,
                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": existing_gst.pk,

                            "gst_no": gst_no,  # Corrected this line
                            "pancard_no": pancard_no,
                            "date_of_establishment": date_of_establishment,
                        },
                    )
            else:
                messages.error(
                    request,
                    "First, you need to complete the client verification and registration page.",
                )
                return redirect("client-list")

class ClientOnboardingStepTwo(View):
    def post(self, request):
        onboarding_gst_verify = self.request.POST.get("onboarding_gst_verify")
        first_company_type = self.request.POST.get("first_company_type")
        industry_type = self.request.POST.get("industry_type")
        website_link = self.request.POST.get("website_link")

        company_type_error = (
            "Company Type is required"
            if not first_company_type
            else ""
        )
        website_link_error = ""
        industry_type_error = "Industry Type is required" if not industry_type else ""

        if any([company_type_error, website_link_error, industry_type_error]):
            onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                pk=onboarding_gst_verify
            )
            bussiness_data = RequestBussinessRegister.objects.get(
                pk=onboarding_gst_verify_instance.request_user.id
            )
            return render(
                request,
                "useraccount/user.html",
                {
                    "company_type_error": company_type_error,
                    "website_link_error": website_link_error,
                    "industry_type_error": industry_type_error,

                    "first_company_type": first_company_type,
                    "industry_type": industry_type,
                    "website_link": website_link,

                    "client_id": bussiness_data.pk,
                    "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                },
            )
        else:
            if onboarding_gst_verify:
                onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                    pk=onboarding_gst_verify
                )
                bussiness_data = RequestBussinessRegister.objects.get(
                    pk=onboarding_gst_verify_instance.request_user.id
                )

                is_business_details_exists = OnboardingBussinessDetails.objects.filter(
                    onboarding_gst_verify=onboarding_gst_verify_instance
                ).exists()
                if not is_business_details_exists:
                    business_model_data = OnboardingBussinessDetails.objects.create(
                        onboarding_gst_verify=onboarding_gst_verify_instance,
                        first_company_type=first_company_type,
                        industry_type=industry_type,
                        website_link=website_link,
                    )
                    messages.success(
                        request,
                        "Business Details Successfully Completed. Please complete the Bussiness Verification page and the rest of the process.",
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business_model_data.pk,
                        },
                    )
                else:
                    existing_business_model_data = OnboardingBussinessDetails.objects.get(
                        onboarding_gst_verify=onboarding_gst_verify_instance
                    )
                    messages.error(
                        request,
                        "Business details Verification already Completed, Please complete the Bussiness Verification page and the rest of the process.",
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "company_type_error": company_type_error,
                            "website_link_error": website_link_error,
                            "industry_type_error": industry_type_error,
                            "first_company_type": first_company_type,
                            "industry_type": industry_type,
                            "website_link": website_link,

                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": existing_business_model_data.pk,
                        },
                    )
            else:
                messages.error(
                    request, "First, you need to complete the gst verification page."
                )
                return redirect("client-list")

class ClientOnboardingStepThree(View):
    def post(self, request):
        onboarding_bussiness_details = self.request.POST.get(
            "onboarding_bussiness_details"
        )
   
        upload_pan = self.request.FILES.get("upload_pan")
        upload_gst = self.request.FILES.get("upload_gst")
        certificate_of_corporation = self.request.FILES.get("certificate_of_corporation")
        msme = self.request.FILES.get("msme")
        authorization_letter = self.request.FILES.get("authorization_letter")
        aadhar = self.request.FILES.get("aadhar")

        upload_pan_error = "Upload Pancard is required" if not upload_pan else ""

        upload_gst_error = "Upload GST is required" if not upload_gst else ""
        certificate_of_corporation_error = (
            "Upload GST is required" if not certificate_of_corporation else ""
        )
        msme_error = "Upload GST is required" if not msme else ""
        authorization_letter_error = (
            "Upload GST is required" if not authorization_letter else ""
        )
        aadhar_error = (
            "Upload GST is required" if not aadhar else ""
        )

        if (upload_pan_error or upload_gst_error or aadhar_error or authorization_letter_error or msme_error or certificate_of_corporation_error):

            business__detail_data = OnboardingBussinessDetails.objects.get(
                pk=onboarding_bussiness_details
            )
            onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                pk=business__detail_data.onboarding_gst_verify.id
            )
            bussiness_data = RequestBussinessRegister.objects.get(
                pk=onboarding_gst_verify_instance.request_user.id
            )
            return render(
                request,
                "useraccount/user.html",
                {
                    "upload_pan_error": upload_pan_error,
                    "upload_gst_error": upload_gst_error,
                    "aadhar_error": aadhar_error,
                    "authorization_letter_error": authorization_letter_error,
                    "msme_error": msme_error,
                    "certificate_of_corporation_error": certificate_of_corporation_error,

                    "upload_pan": upload_pan,
                    "upload_gst": upload_gst,
                    "certificate_of_corporation": certificate_of_corporation,
                    "aadhar": aadhar,
                    "authorization_letter": authorization_letter,
                    "msme": msme,

                    "client_id": bussiness_data.pk,
                    "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                    "bussiness_details": business__detail_data.pk,
                },
            )
        else:
            if onboarding_bussiness_details:
                business__detail_data = OnboardingBussinessDetails.objects.get(
                    pk=onboarding_bussiness_details
                )
                onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                    pk=business__detail_data.onboarding_gst_verify.id
                )
                bussiness_data = RequestBussinessRegister.objects.get(
                    pk=onboarding_gst_verify_instance.request_user.id
                )
                bank_check_data = OnboardingBankDetails.objects.filter(
                    onboarding_bussiness_details=business__detail_data
                ).exists()
                if not bank_check_data:
                    bank_data = OnboardingBankDetails(
                        onboarding_bussiness_details=business__detail_data,
                        upload_pan=upload_pan,
                        upload_gst=upload_gst,
                        certificate_of_corporation=certificate_of_corporation,
                        msme=msme,
                        authorization_letter=authorization_letter,
                        aadhar=aadhar,
                    )
                    bank_data.save()

                    messages.success(
                        request,
                        "Bank Details Verification Successfully Completed. Please complete the Communications page.",
                    )

                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details": bank_data.pk
                        },
                    )
                else:
                    existing_bank_data = (
                        OnboardingBankDetails.objects.get(
                            onboarding_bussiness_details=onboarding_bussiness_details
                        )
                    )

                    messages.error(request," Bank Details Verification already Completed, Please complete the Communications page.",)

                    return render(request,"useraccount/user.html",
                        {
                            "upload_pan": upload_pan,
                            "upload_gst": upload_gst,
                            "certificate_of_corporation": certificate_of_corporation,
                            "msme": msme,
                            "authorization_letter": authorization_letter,
                            "aadhar": aadhar,

                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details": existing_bank_data.pk
                        },
                    )
            else:
                messages.error(
                    request, "First, Complete the Bussiness Verification page."
                )
                return redirect("client-list")
class ClientOnboardingStepFour(View):
    def post(self, request):
        onboarding_bank_details = self.request.POST.get("onboarding_bank_details")

        communication_postal_code = request.POST.get("communication_postal_code")
        communication_country = request.POST.get("communication_country")
        communication_state = request.POST.get("communication_state")
        communication_city = request.POST.get("communication_city")
        communication_address = request.POST.get("communication_address")

        communication_address_error = ""
        if not communication_address:
            communication_address_error = "This address is required"

        communication_city_error = ""
        if not communication_city:
            communication_city_error = "City is required."

        communication_state_error = ""
        if not communication_state:
            communication_state_error = "State is required."

        communication_country_error = ""
        if not communication_country:
            communication_country_error = "Country is required."

        communication_postal_code_error = ""
        if not communication_postal_code:
            communication_postal_code_error = "Pin Code is required."
        elif not is_valid_pin_code(communication_postal_code):
            communication_postal_code_error = "Pin Code must be a 6-digit number."

        if (communication_country_error or communication_city_error or communication_state_error or communication_postal_code_error or communication_address_error
        ):
            bank_check_data = OnboardingBankDetails.objects.get(
                pk=onboarding_bank_details
            )
            business__detail_data = OnboardingBussinessDetails.objects.get(
                pk=bank_check_data.onboarding_bussiness_details.id
            )
            onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                pk=business__detail_data.onboarding_gst_verify.id
            )
            bussiness_data = RequestBussinessRegister.objects.get(
                pk=onboarding_gst_verify_instance.request_user.id
            )
            return render(
                request,
                "useraccount/user.html",
                {
                    "communication_country_error": communication_country_error,
                    "communication_city_error": communication_city_error,
                    "communication_state_error": communication_state_error,
                    "communication_postal_code_error": communication_postal_code_error,
                    "communication_address_error": communication_address_error,

                    "communication_address": communication_address,
                    "communication_country": communication_country,
                    "communication_state": communication_state,
                    "communication_city": communication_city,
                    "communication_postal_code": communication_postal_code,

                    "client_id": bussiness_data.pk,
                    "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                    "bussiness_details": business__detail_data.pk,
                    "onboarding_bank_details": bank_check_data.pk,

                },
            )
        else:
            if onboarding_bank_details:
                bank_check_data = OnboardingBankDetails.objects.get(
                    pk=onboarding_bank_details
                )
                business__detail_data = OnboardingBussinessDetails.objects.get(
                    pk=bank_check_data.onboarding_bussiness_details.id
                )
                onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                    pk=business__detail_data.onboarding_gst_verify.id
                )
                bussiness_data = RequestBussinessRegister.objects.get(
                    pk=onboarding_gst_verify_instance.request_user.id
                )
                onboarding_comm_details = OnboardingCommunication.objects.filter(
                    onboarding_bank_details=bank_check_data
                ).exists()
                if not onboarding_comm_details:
                    Communication_data = OnboardingCommunication(
                        onboarding_bank_details=bank_check_data,
                        communication_address=communication_address,
                        communication_city=communication_city,
                        communication_state=communication_state,
                        communication_country=communication_country,
                        communication_postal_code=communication_postal_code,
                    )
                    Communication_data.save()

                    messages.success(
                        request,
                        "Onboarding Communication Successfully Completed. Please complete the Register Address page.",
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details":bank_check_data.pk,
                            "onboarding_comm_details":Communication_data.pk
                        },
                    )
                else:
                    existing_communication_data = (
                        OnboardingCommunication.objects.get(
                            onboarding_bank_details=bank_check_data
                        )
                    )
                    messages.error(
                        request,
                        "Onboarding Communication already Completed, Please complete the Register Address page.",
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "communication_address" : existing_communication_data.communication_address,
                            "communication_city" : existing_communication_data.communication_city,
                            "communication_state" : existing_communication_data.communication_state,
                            "communication_country" : existing_communication_data.communication_country,
                            "communication_postal_code" : existing_communication_data.communication_postal_code,

                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details":bank_check_data.pk,
                            "onboarding_comm_details":existing_communication_data.pk
                        },
                    )
            else:
                messages.error(
                    request, "First, Complete the Bank Verification page."
                )
                return redirect("client-list")
class ClientOnboardingStepFive(View):
    def post(self, request):
        onboarding_comm_details = self.request.POST.get("onboarding_comm_details")

        reg_country = request.POST.get("reg_country")
        reg_state = request.POST.get("reg_state")
        reg_postal_code = request.POST.get("reg_postal_code")
        reg_city = request.POST.get("reg_city")
        reg_address = request.POST.get("reg_address")

        print("reg_country:", reg_country)
        print("reg_state:", reg_state)
        print("reg_postal_code:", reg_postal_code)
        print("reg_city:", reg_city)
        print("reg_address:", reg_address)

        reg_city_error = ""
        if not reg_city:
            reg_city_error = "This City is required"

        reg_address_error = ""
        if not reg_address:
            reg_address_error = "This Address is required."

        reg_state_error = ""
        if not reg_state:
            reg_state_error = "State is required."

        reg_country_error = ""
        if not reg_country:
            reg_country_error = "Country is required."

        reg_postal_code_error = ""
        if not reg_postal_code:
            reg_postal_code_error = "Pin Code is required."
        elif not is_valid_pin_code(reg_postal_code):
            reg_postal_code_error = "Pin Code must be a 6-digit number."

        if (reg_city_error or reg_country_error or reg_state_error or reg_postal_code_error or reg_address_error):
            onboarding_communication_details = OnboardingCommunication.objects.get(
                pk=onboarding_comm_details
            )
            bank_check_data = OnboardingBankDetails.objects.get(
                pk=onboarding_communication_details.onboarding_bank_details.pk
            )
            business__detail_data = OnboardingBussinessDetails.objects.get(
                pk=bank_check_data.onboarding_bussiness_details.id
            )
            onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                pk=business__detail_data.onboarding_gst_verify.id
            )
            bussiness_data = RequestBussinessRegister.objects.get(
                pk=onboarding_gst_verify_instance.request_user.id
            )
            return render(
                request,
                "useraccount/user.html",
                {
                    "reg_city_error": reg_city_error,
                    "reg_country_error": reg_country_error,
                    "reg_state_error": reg_state_error,
                    "reg_postal_code_error": reg_postal_code_error,
                    "reg_address_error": reg_address_error,

                    "reg_city": reg_city,
                    "reg_country": reg_country,
                    "reg_state": reg_state,
                    "reg_postal_code": reg_postal_code,
                    "reg_address": reg_address,

                    "client_id": bussiness_data.pk,
                    "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                    "bussiness_details": business__detail_data.pk,
                    "onboarding_bank_details": bank_check_data.pk,
                    "onboarding_comm_details": onboarding_communication_details.pk

                },
            )
        else:
            if onboarding_comm_details:
                onboarding_communication_details = OnboardingCommunication.objects.get(
                    pk=onboarding_comm_details
                )
                bank_check_data = OnboardingBankDetails.objects.get(
                    pk=onboarding_communication_details.onboarding_bank_details.pk
                )
                business__detail_data = OnboardingBussinessDetails.objects.get(
                    pk=bank_check_data.onboarding_bussiness_details.id
                )
                onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                    pk=business__detail_data.onboarding_gst_verify.id
                )
                bussiness_data = RequestBussinessRegister.objects.get(
                    pk=onboarding_gst_verify_instance.request_user.id
                )
                onboarding_reg_details = OnboardingRegisteredAddress.objects.filter(
                    onboarding_comm_details=onboarding_comm_details
                ).exists()
                if not onboarding_reg_details:
                    register_address_data = OnboardingRegisteredAddress(
                        onboarding_comm_details=onboarding_communication_details,
                        reg_postal_code=reg_postal_code,
                        reg_country=reg_country,
                        reg_state=reg_state,
                        reg_city=reg_city,
                        reg_address=reg_address
                    )
                    register_address_data.save()

                    messages.success(
                        request,
                        "Onboarding Register Address Successfully Completed. Please complete the Onboarding Warehouse page.",
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details": bank_check_data.pk,
                            "onboarding_comm_details": onboarding_communication_details.pk,
                            "onboarding_reg_details": register_address_data.pk,
                        },
                    )
                else:
                    existing_reg_data = (
                        OnboardingRegisteredAddress.objects.get(
                            onboarding_comm_details=onboarding_communication_details
                        )
                    )
                    messages.error(
                        request,
                        "Onboarding Register Address already Completed, Please complete the Warehouse page.",
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "reg_address": existing_reg_data.reg_address,
                            "reg_city": existing_reg_data.reg_city,
                            "reg_state": existing_reg_data.reg_state,
                            "reg_country": existing_reg_data.reg_country,
                            "reg_postal_code": existing_reg_data.reg_postal_code,

                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details": bank_check_data.pk,
                            "onboarding_comm_details": onboarding_communication_details.pk,
                            "onboarding_reg_details": existing_reg_data.pk
                        },
                    )
            else:
                messages.error(
                    request, "First, Complete the Communication Verification page."
                )
                return redirect("client-list")
class ClientOnboardingStepSix(View):
    def post(self, request):
        onboarding_reg_details = self.request.POST.get("onboarding_reg_details")

        warehouse_address = request.POST.get("warehouse_address")
        warehouse_country = request.POST.get("warehouse_country")
        warehouse_state = request.POST.get("warehouse_state")
        warehouse_city = request.POST.get("warehouse_city")
        warehouse_postal_code = request.POST.get("warehouse_postal_code")

        warehouse_address_error = ""
        if not warehouse_address:
            warehouse_address_error = "This address is required"

        warehouse_city_error = ""
        if not warehouse_city:
            warehouse_city_error = "City is required."

        warehouse_state_error = ""
        if not warehouse_state:
            warehouse_state_error = "State is required."

        warehouse_country_error = ""
        if not warehouse_country:
            warehouse_country_error = "Country is required."

        warehouse_postal_code_error = ""
        if not warehouse_postal_code:
            warehouse_postal_code_error = "Pin Code is required."
        elif not is_valid_pin_code(warehouse_postal_code):
            warehouse_postal_code_error = "Pin Code must be a 6-digit number."

        if (warehouse_country_error or warehouse_city_error or warehouse_state_error or warehouse_postal_code_error or warehouse_address_error
        ):
            onboarding_reg_details = OnboardingRegisteredAddress.objects.get(
                pk=onboarding_reg_details
            )
            onboarding_communication_details = OnboardingCommunication.objects.get(
                pk=onboarding_reg_details.onboarding_comm_details.id
            )
            bank_check_data = OnboardingBankDetails.objects.get(
                pk=onboarding_communication_details.onboarding_bank_details.pk
            )
            business__detail_data = OnboardingBussinessDetails.objects.get(
                pk=bank_check_data.onboarding_bussiness_details.id
            )
            onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                pk=business__detail_data.onboarding_gst_verify.id
            )
            bussiness_data = RequestBussinessRegister.objects.get(
                pk=onboarding_gst_verify_instance.request_user.id
            )
            return render(
                request,
                "useraccount/user.html",
                {
                    "warehouse_country_error": warehouse_country_error,
                    "warehouse_city_error": warehouse_city_error,
                    "warehouse_state_error": warehouse_state_error,
                    "warehouse_postal_code_error": warehouse_postal_code_error,
                    "warehouse_address_error": warehouse_address_error,

                    "warehouse_address":warehouse_address,
                    "warehouse_country":warehouse_country,
                    "warehouse_state":warehouse_state,
                    "warehouse_city":warehouse_city,
                    "warehouse_postal_code":warehouse_postal_code,

                    "client_id": bussiness_data.pk,
                    "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                    "bussiness_details": business__detail_data.pk,
                    "onboarding_bank_details": bank_check_data.pk,
                    "onboarding_comm_details": onboarding_communication_details.pk,
                    "onboarding_reg_details": onboarding_reg_details.pk,

                },
            )
        else:
            if onboarding_reg_details:

                reg_data = OnboardingRegisteredAddress.objects.get(
                    pk=onboarding_reg_details
                )
                communication_data = OnboardingCommunication.objects.get(
                    pk=reg_data.onboarding_comm_details.id
                )
                bank_check_data = OnboardingBankDetails.objects.get(
                    pk=communication_data.onboarding_bank_details.id
                )
                business__detail_data = OnboardingBussinessDetails.objects.get(
                    pk=bank_check_data.onboarding_bussiness_details.id
                )
                onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                    pk=business__detail_data.onboarding_gst_verify.id
                )
                bussiness_data = RequestBussinessRegister.objects.get(
                    pk=onboarding_gst_verify_instance.request_user.id
                )
                onboarding_warehouse_details = WarehouseAddress.objects.filter(
                    onboarding_reg_details=reg_data
                ).exists()
                if not onboarding_warehouse_details:
                    warehouse_data = WarehouseAddress(
                        onboarding_reg_details=reg_data,
                        warehouse_address=warehouse_address,
                        warehouse_city=warehouse_city,
                        warehouse_state=warehouse_state,
                        warehouse_country=warehouse_country,
                        warehouse_postal_code=warehouse_postal_code,
                    )
                    warehouse_data.save()

                    messages.success(
                        request,
                        "Onboarding Warehouse Successfully Completed. Please complete the Onboarding Outlet page.",
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details":bank_check_data.pk,
                            "onboarding_comm_details":communication_data.pk,
                            "onboarding_reg_details":reg_data.pk,
                            "onboarding_warehouse_details":warehouse_data.pk
                        },
                    )
                else:
                    existing_warehouse_data = (
                        WarehouseAddress.objects.get(
                            onboarding_reg_details=reg_data
                        )
                    )
                    messages.error(
                        request,
                        "Onboarding Warehouse already Completed, Please complete the Outlet page.",
                    )
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "communication_address": existing_warehouse_data.warehouse_address,
                            "communication_city": existing_warehouse_data.warehouse_city,
                            "communication_state": existing_warehouse_data.warehouse_state,
                            "communication_country": existing_warehouse_data.warehouse_country,
                            "communication_postal_code": existing_warehouse_data.warehouse_postal_code,

                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details": bank_check_data.pk,
                            "onboarding_comm_details": communication_data.pk,
                            "onboarding_reg_details": reg_data.pk,
                            "onboarding_warehouse_details": existing_warehouse_data.pk,
                        },
                    )
            else:
                messages.error(
                    request, "First, Complete the Register Address page."
                )
                return redirect("client-list")
class ClientOnboardingStepSeven(View):
    def post(self, request):
        onboarding_warehouse_details = self.request.POST.get("onboarding_warehouse_details")

        outlet_address = request.POST.get("outlet_address")
        outlet_city = request.POST.get("outlet_city")
        outlet_state = request.POST.get("outlet_state")
        outlet_country = request.POST.get("outlet_country")
        outlet_postal_code = request.POST.get("outlet_postal_code")

        outlet_address_error = ""
        if not outlet_address:
            outlet_address_error = "This address is required"

        outlet_city_error = ""
        if not outlet_city:
            outlet_city_error = "City is required."

        outlet_state_error = ""
        if not outlet_state:
            outlet_state_error = "State is required."

        outlet_country_error = ""
        if not outlet_country:
            outlet_country_error = "Country is required."

        outlet_postal_code_error = ""
        if not outlet_postal_code:
            outlet_postal_code_error = "Pin Code is required."
        elif not is_valid_pin_code(outlet_postal_code):
            outlet_postal_code_error = "Pin Code must be a 6-digit number."

        if (
            outlet_country_error or outlet_city_error or outlet_state_error or outlet_postal_code_error or outlet_address_error
        ):
            return render(
                request,
                "useraccount/user.html",
                {
                    "outlet_country_error": outlet_country_error,
                    "outlet_city_error": outlet_city_error,
                    "outlet_state_error": outlet_state_error,
                    "outlet_postal_code_error": outlet_postal_code_error,
                    "outlet_address_error": outlet_address_error,

                    "outlet_address": outlet_address,
                    "outlet_country": outlet_country,
                    "outlet_state": outlet_state,
                    "outlet_city": outlet_city,
                    "outlet_postal_code": outlet_postal_code,

                },
            )
        else:
            if onboarding_warehouse_details:
                try:
                    with transaction.atomic():
                        onboarding_warehouse_details = WarehouseAddress.objects.get(
                            pk=onboarding_warehouse_details
                        )
                        reg_data = OnboardingRegisteredAddress.objects.get(
                            pk=onboarding_warehouse_details.onboarding_reg_details.id
                        )
                        onboarding_communication_details = OnboardingCommunication.objects.get(
                            pk=reg_data.onboarding_comm_details.id
                        )
                        bank_check_data = OnboardingBankDetails.objects.get(
                            pk=onboarding_communication_details.onboarding_bank_details.pk
                        )
                        business__detail_data = OnboardingBussinessDetails.objects.get(
                            pk=bank_check_data.onboarding_bussiness_details.id
                        )
                        onboarding_gst_verify_instance = OnboardingGstVerify.objects.get(
                            pk=business__detail_data.onboarding_gst_verify.id
                        )
                        bussiness_data = RequestBussinessRegister.objects.get(
                            pk=onboarding_gst_verify_instance.request_user.id
                        )
                        onboarding_outlet_details = OutletAddress.objects.filter(
                            onboarding_warehouse_details=onboarding_warehouse_details
                        ).exists()

                        if not onboarding_outlet_details:
                            outlet_data = OutletAddress(
                                onboarding_warehouse_details=onboarding_warehouse_details,
                                outlet_postal_code=outlet_postal_code,
                                outlet_country=outlet_country,
                                outlet_state=outlet_state,
                                outlet_city=outlet_city,
                                outlet_address=outlet_address
                            )
                            outlet_data.save()

                            warehouse_model_data = WarehouseAddress.objects.get(pk=outlet_data.onboarding_warehouse_details.id)
                            reg_model_data = OnboardingRegisteredAddress.objects.get(pk=warehouse_model_data.onboarding_reg_details.id)
                            communication_model_data = OnboardingCommunication.objects.get(pk=reg_model_data.onboarding_comm_details.id)
                            bank_model_data = OnboardingBankDetails.objects.get(pk=communication_model_data.onboarding_bank_details.id)
                            business_model_data = OnboardingBussinessDetails.objects.get(pk=bank_model_data.onboarding_bussiness_details.id)
                            gst_model_data = OnboardingGstVerify.objects.get(pk=business_model_data.onboarding_gst_verify.id)
                            register_buss_model_data = RequestBussinessRegister.objects.get(pk=gst_model_data.request_user.id)

                            primary_contact_person = (
                                register_buss_model_data.primary_contact_person
                            )
                            name_parts = primary_contact_person.split(" ", 1)

                            if len(name_parts) == 2:
                                first_name, last_name = name_parts
                            else:
                                first_name = primary_contact_person
                                last_name = ""
                            password = User.objects.make_random_password()
                            user = User(
                                first_name=first_name,
                                last_name=last_name,
                                username=register_buss_model_data.email,
                                email=register_buss_model_data.email,
                                password=make_password(password),
                            )
                            print("password:", password)
                            user.save()

                            # Add User to Group
                            user_group, created = Group.objects.get_or_create(name="client")
                            user.groups.add(user_group)

                            client_details = ClientDetails(
                                user=user,
                                designation=register_buss_model_data.designation,
                                primary_contact_person=register_buss_model_data.primary_contact_person,
                                mobile_no=register_buss_model_data.mobile_number,

                                gst_no=gst_model_data.gst_number,
                                pancard_no=gst_model_data.pancard_no,
                                # address_line1=gst_model_data.first_address,
                                # address_line2=gst_model_data.second_address,
                                # city=gst_model_data.city,
                                # state=gst_model_data.state,
                                # country=gst_model_data.country,
                                # pin_code=gst_model_data.postal_code,
                                date_of_establishment=gst_model_data.date_of_establishment,
                                company_name=register_buss_model_data.bussiness_name,

                                first_company_type=business_model_data.first_company_type,
                                # second_company_type=business_model_data.second_company_type,
                                industry_type=business_model_data.industry_type,
                                website_link=business_model_data.website_link,

                                # alternative_mobile=alternative_model_data.alternative_mobile,
                                # alternative_email=alternative_model_data.alternative_email,
                                # alternative_designation=alternative_model_data.alternative_designation,
                                # alternative_person_name=alternative_model_data.alternative_person_name,

                                upload_pan=bank_model_data.upload_pan,
                                upload_gst=bank_model_data.upload_gst,
                                certificate_of_corporation=bank_model_data.certificate_of_corporation,
                                msme=bank_model_data.msme,
                                authorization_letter=bank_model_data.authorization_letter,
                                adhaar=bank_model_data.aadhar,

                                communication_postal_code=communication_model_data.communication_postal_code,
                                communication_country=communication_model_data.communication_country,
                                communication_state=communication_model_data.communication_state,
                                communication_city=communication_model_data.communication_city,
                                communication_address=communication_model_data.communication_address,

                                reg_postal_code=reg_model_data.reg_postal_code,
                                reg_country=reg_model_data.reg_country,
                                reg_state=reg_model_data.reg_state,
                                reg_city=reg_model_data.reg_city,
                                reg_address=reg_model_data.reg_address,

                                warehouse_postal_code=warehouse_model_data.warehouse_postal_code,
                                warehouse_country=warehouse_model_data.warehouse_country,
                                warehouse_state=warehouse_model_data.warehouse_state,
                                warehouse_city=warehouse_model_data.warehouse_city,
                                warehouse_address=warehouse_model_data.warehouse_address,

                                outlet_postal_code=outlet_data.outlet_postal_code,
                                outlet_country=outlet_data.outlet_country,
                                outlet_state=outlet_data.outlet_state,
                                outlet_city=outlet_data.outlet_city,
                                outlet_address=outlet_data.outlet_address

                            )
                            # Create a ClientDetails object and associate it with the user
                            client_details.save()
                            cou = Country.objects.filter(name="Republic of India").first()

                            if len(name_parts) == 2:
                                first_name, last_name = name_parts
                            else:
                                first_name = primary_contact_person
                                last_name = ""

                            user_add = UserAddress.objects.create(
                                user=user,
                                first_name=first_name,
                                last_name=last_name,
                                email=client_details.user.email,
                                line1=client_details.reg_address,
                                # line2=client_details.address_line2,
                                line4=client_details.reg_city,
                                state=client_details.reg_state,
                                postcode=client_details.reg_postal_code,
                                country=cou,
                                phone_number=client_details.mobile_no,
                            )
                            try:
                                # Notify the client with their login details
                                subject = "You are Registered on Oneup Brand Site"
                                message = f"This is Email and Password:\n\nEmail: {client_details.user.email}\nPassword: {password}\n"
                                from_email = settings.EMAIL_HOST_USER
                                to_email = [client_details.user.email]

                                send_mail(subject, message, from_email, to_email)
                                # Send notification mail
                                self.send_notification_mail(client_details)
                            except Exception as e:
                                logger.error("Error occurred while sending the email: %s", e, exc_info=True)
                                # Rollback changes if email sending fails
                                if client_details.id:
                                    client_details.delete()
                                if user.id:
                                    user.delete()
                                if user_add.id:
                                    user_add.delete()

                                messages.error(request, f"An error occurred while sending the email: {e}")
                                return render(
                                    request,
                                    "useraccount/user.html",
                                    {
                                        "outlet_city": outlet_city,
                                        "outlet_country": outlet_country,
                                        "outlet_state": outlet_state,
                                        "outlet_postal_code": outlet_postal_code,
                                        "outlet_address": outlet_address,

                                        "client_id": bussiness_data.pk,
                                        "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                                        "bussiness_details": business__detail_data.pk,
                                        "onboarding_bank_details": bank_check_data.pk,
                                        "onboarding_comm_details": communication_model_data.pk,
                                        "onboarding_reg_details": reg_model_data.pk,
                                        "onboarding_warehouse_details": warehouse_model_data.pk,
                                    },
                                )

                            messages.success(
                                self.request,
                                _(
                                    f"Onboarding Process completed successfully. And the mail has also been sent to this email:."
                                    + client_details.user.email
                                ),
                            )
                            return redirect("client-list")
                        else:

                            user_exists = User.objects.filter(groups__name="client", email=bussiness_data.email).exists()
                            client_data_exist_or_not = ClientDetails.objects.filter(user=user_exists, mobile_no=bussiness_data.mobile_number).exists()
                            try:
                                if client_data_exist_or_not:
                                    # Notify the client with their login details
                                    subject = "You are Registered on Oneup Brand Site"
                                    message = f"This is Email and Password:\n\nEmail: {client_data_exist_or_not.user.email}\nPassword: {user_exists.password}\n"
                                    from_email = settings.EMAIL_HOST_USER
                                    to_email = [client_data_exist_or_not.user.email]

                                    send_mail(subject, message, from_email, to_email)
                                    # Send notification mail
                                    self.send_notification_mail(client_data_exist_or_not)
                                    messages.success(
                                        self.request,
                                        _(f"You have already completed Onboarding Process."),
                                    )
                                    return redirect("client-list")
                                else:
                                    existing_outlet_details = OutletAddress.objects.get(
                                        onboarding_warehouse_details=onboarding_warehouse_details
                                    )
                                    existing_outlet_details.delete()
                                    messages.error(self.request,_(f"Onboarding process not completed. Because an error occurred while creating the client."),)

                                    return render(
                                        request,
                                        "useraccount/user.html",
                                        {
                                            "outlet_city": outlet_city,
                                            "outlet_country": outlet_country,
                                            "outlet_state": outlet_state,
                                            "outlet_postal_code": outlet_postal_code,
                                            "outlet_address": outlet_address,

                                            "client_id": bussiness_data.pk,
                                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                                            "bussiness_details": business__detail_data.pk,
                                            "onboarding_bank_details": bank_check_data.pk,
                                            "onboarding_comm_details": onboarding_communication_details.pk,
                                            "onboarding_reg_details": reg_data.pk,
                                            "onboarding_warehouse_details": onboarding_warehouse_details.pk,
                                        },
                                    )
                            except Exception as e:
                                messages.error(self.request, _("An error occurred: %s" % str(e)))

                except Exception as e:
                    # Handle exceptions and rollback changes
                    messages.error(self.request, _("An error occurred: %s" % str(e)))
                    return render(
                        request,
                        "useraccount/user.html",
                        {
                            "outlet_city": outlet_city,
                            "outlet_country": outlet_country,
                            "outlet_state": outlet_state,
                            "outlet_postal_code": outlet_postal_code,
                            "outlet_address": outlet_address,

                            "client_id": bussiness_data.pk,
                            "onboarding_gst_verify": onboarding_gst_verify_instance.pk,
                            "bussiness_details": business__detail_data.pk,
                            "onboarding_bank_details": bank_check_data.pk,
                            "onboarding_comm_details":onboarding_communication_details.pk,
                            "onboarding_reg_details":reg_data.pk,
                            "onboarding_warehouse_details":onboarding_warehouse_details.pk,
                        },
                    )
            else:
                messages.error(
                    self.request,
                    _(
                        "First, Complete the Onboarding Warehouse page."
                    ),
                )
                return redirect("client-list")

    def send_notification_mail(self, client_details):
        subject = "New Client Registered on Site"
        message = (
            f"Here is a new client registered on OneUp Brand:\n\n"
            f"Company Name: {client_details.company_name}\n"
            f"Email: {client_details.user.email}\n"
            f"Mobile Number: {client_details.mobile_no}\n"
        )
        from_email = settings.EMAIL_HOST_USER
        to_email = [settings.EMAIL_HOST_USER]

        send_mail(subject, message, from_email, to_email)

from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib import messages
from datetime import datetime


# Helper functions
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Date format must be YYYY-MM-DD")


class EditClientView(View):
    template_name = "useraccount/edit_client.html"

    def get(self, request, pk):
        user = User.objects.get(pk=pk)
        print("user=", user)
        client_user = ClientDetails.objects.get(user__id=pk)
        return render(request, self.template_name, {"client_user": client_user})

    def post(self, request, pk):
        print("code here")
        user = User.objects.get(pk=pk)

        # user.email = request.POST.get("email")
        new_email = request.POST.get("email")

        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.date_joined = timezone.now()

        client_user = ClientDetails.objects.get(user__id=pk)
        print(client_user, "client_user")

        client_user.primary_contact_person = request.POST.get("primary_contact_person")
        client_user.designation = request.POST.get("designation")
        # client_user.mobile_no = request.POST.get("mobile_no")
        new_mobile =request.POST.get("mobile_no")
        client_user.company_name = request.POST.get("company_name")
        client_user.pancard_no = request.POST.get("pancard_no")
        client_user.gst_no = request.POST.get("gst_no")
        if len(self.request.POST.get("gst_no").lstrip()) == 0 or self.request.POST.get("gst_no") == "None":
            client_user.gst_no = None

        # Validate dates
        try:
            if request.POST.get("date_of_birth"):
                client_user.date_of_birth = parse_date(
                    request.POST.get("date_of_birth")
                )
            if request.POST.get("date_of_establishment"):
                client_user.date_of_establishment = parse_date(
                    request.POST.get("date_of_establishment")
                )
        except ValidationError as e:
            messages.error(request, str(e))
            return self.render_form(request, user, client_user)

        client_user.gender = request.POST.get("gender")
        client_user.current_date = timezone.now()

        client_user.first_company_type = request.POST.get("first_company_type")
        client_user.industry_type = request.POST.get("industry_type")
        client_user.website_link = request.POST.get("website_link")


        if request.FILES.get("upload_pan"):
            client_user.upload_pan = request.FILES.get("upload_pan")

        if request.FILES.get("upload_gst"):
            client_user.upload_gst = request.FILES.get("upload_gst")

        if request.FILES.get("certificate_of_corporation"):
            client_user.certificate_of_corporation = request.FILES.get(
                "certificate_of_corporation"
            )

        if request.FILES.get("msme"):
            client_user.msme = request.FILES.get("msme")

        if request.FILES.get("authorization_letter"):
            client_user.authorization_letter = request.FILES.get("authorization_letter")

        if request.FILES.get("adhaar"):
            client_user.adhaar = request.FILES.get("adhaar")


        client_user.communication_postal_code = self.request.POST.get("communication_postal_code")
        client_user.communication_country = self.request.POST.get("communication_country")
        client_user.communication_state = self.request.POST.get("communication_state")
        client_user.communication_city = self.request.POST.get("communication_city")
        client_user.communication_address = self.request.POST.get("communication_address")

        # test
        client_user.reg_postal_code = self.request.POST.get("reg_postal_code")
        client_user.reg_country = self.request.POST.get("reg_country")
        client_user.reg_state= self.request.POST.get("reg_state")
        client_user.reg_city = self.request.POST.get("reg_city")
        client_user.reg_address = self.request.POST.get("reg_address")

        # Warehouse part
        client_user.warehouse_postal_code = self.request.POST.get("warehouse_postal_code")
        client_user.warehouse_country = self.request.POST.get("warehouse_country")
        client_user.warehouse_state = self.request.POST.get("warehouse_state")
        client_user.warehouse_city = self.request.POST.get("warehouse_city")
        client_user.warehouse_address = self.request.POST.get("warehouse_address")

        # Outlet part
        client_user.outlet_postal_code = self.request.POST.get("outlet_postal_code")
        client_user.outlet_country = self.request.POST.get("outlet_country")
        client_user.outlet_state = self.request.POST.get("outlet_state")
        client_user.outlet_city = self.request.POST.get("outlet_city")
        client_user.outlet_address = self.request.POST.get("outlet_address")


        email_error = ""
        if not new_email:
            email_error = "Email is required."
        elif not is_valid_email(new_email):
            email_error = "Please enter a valid email address."
        else:
            if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                email_error = "This email is already in use. Please use a different email address."

            else:
                user.email = new_email

        primary_contact_person_error = ""

        # if not client_user.primary_contact_person:
        #     primary_contact_person_error = (
        #         "Person Name is required and can only contain letters."
        #     )

        mobile_error = ""
        if not client_user.mobile_no:
            mobile_error = "Mobile Number is required."
        # elif not is_valid_mobile_number(client_user.mobile_no):
        #     mobile_error = "Mobile Number must be a 10-digit number."
        # elif RequestBussinessRegister.objects.filter(mobile_number=new_mobile).exists():
        #         print("innrer code error")
        #         mobile_error = "This mobile number is already in use. Please use a different mobile number ."
        #         print(mobile_error,"here mobile_error")
        else:
            client_user.mobile_no = new_mobile

        print(mobile_error,"mobile_no_error test")

        company_name_error = ""
        if not client_user.company_name:
            company_name_error = "Company Name is required."
        # elif not is_valid_text(company_name):
        #     company_name_error = 'Company Name can only contain letters.'

        designation_error = ""
        if not client_user.designation:
            designation_error = "Designation is required"

        pancard_number_error = ""
        if not client_user.pancard_no or client_user.pancard_no == "None":
            pancard_number_error = "pancard number is required"

        gst_no_error = ""
        # if not client_user.gst_no:
        #     gst_no_error = "gst number is required"

        company_type_error = ""
        if not client_user.first_company_type:
            company_type_error = "Company Type is required"

        website_link_error = ""
        # if not client_user.website_link:
        #     website_link_error = 'Website Link is required'

        industry_type_error = ""
        if not client_user.industry_type:
            industry_type_error = "Industry Type is required"

        upload_pan_error = ""
        if not client_user.upload_pan:
            upload_pan_error = "Upload Pancard is required"

        warehouse_address_error = ""
        if not client_user.warehouse_address:
            warehouse_address_error = "Warehouse Address is required"

        upload_gst_error = ""
        # if not client_user.upload_gst:
        #     upload_gst_error = 'Upload Gst is required'

        # certificate_of_corporation_error = (
        #     "Upload GST is required"
        #     if not client_user.certificate_of_corporation
        #     else ""
        # )
        # msme_error = "Upload GST is required" if not client_user.msme else ""
        # authorization_letter_error = (
        #     "Upload GST is required" if not client_user.authorization_letter else ""
        # )
        # cancelation_letter_error = (
        #     "Upload GST is required" if not client_user.cancelation_letter else ""
        # )

        date_of_establishment_error = ""
        if not client_user.date_of_establishment:
            date_of_establishment_error = "Date of Establishment is required"

        communication_address_error = ""
        if not client_user.communication_address:
             communication_address_error = "This address is required"

        reg_address_error = ""
        if not client_user.reg_address:
             reg_address_error = "This address is required"

        if (email_error or upload_gst_error or upload_pan_error or industry_type_error or website_link_error
                or company_type_error or mobile_error or company_name_error
                or designation_error or primary_contact_person_error or pancard_number_error or gst_no_error
                # or cancelation_letter_error # or authorization_letter_error # or msme_error # or certificate_of_corporation_error
                or communication_address_error or reg_address_error or date_of_establishment_error
        ):
            client_user_edit = {
                "email": request.POST.get("email"),
                "email_hidden": request.POST.get("email", client_user.user.email),
                "first_name": request.POST.get("first_name"),
                "last_name": request.POST.get("last_name"),
                "primary_contact_person": request.POST.get("primary_contact_person", client_user.primary_contact_person),
                "designation": request.POST.get("designation", client_user.designation),
                "mobile_no": request.POST.get("mobile_no", client_user.mobile_no),
                "mobile_no_hidden": request.POST.get("mobile_no", client_user.mobile_no),
                "company_name": request.POST.get("company_name", client_user.company_name),
                "first_company_type": request.POST.get("first_company_type", client_user.first_company_type),
                "industry_type": request.POST.get("industry_type", client_user.industry_type),
                "website_link": request.POST.get("website_link", client_user.website_link),

                "upload_pan": request.FILES.get("upload_pan", client_user.upload_pan),
                "upload_gst": request.FILES.get("upload_gst", client_user.upload_gst),
                # "city": request.POST.get("city", client_user.city),
                # "state": request.POST.get("state", client_user.state),
                # "country": request.POST.get("country", client_user.country),
                "date_of_establishment": request.POST.get("date_of_establishment", client_user.date_of_establishment),
                # "pin_code": request.POST.get("pin_code", client_user.pin_code),


                "pancard_no": request.POST.get("pancard_no", client_user.pancard_no),
                "gender": request.POST.get("gender", client_user.gender),
                "date_of_birth": request.POST.get("date_of_birth", client_user.date_of_birth),
                "gst_no": request.POST.get("gst_no", client_user.gst_no),
                "certificate_of_corporation": request.FILES.get("certificate_of_corporation", client_user.certificate_of_corporation),
                "authorization_letter": request.FILES.get("authorization_letter", client_user.authorization_letter),
                "msme": request.FILES.get("msme", client_user.msme),
                "adhaar": request.FILES.get("adhaar", client_user.adhaar),

                # communication
                "communication_postal_code" : request.POST.get("communication_postal_code", client_user.communication_postal_code),
                "communication_country" : request.POST.get("communication_country", client_user.communication_country),
                "communication_state" : request.POST.get("communication_state", client_user.communication_state),
                "communication_city" : request.POST.get("communication_city", client_user.communication_city),
                "communication_address" : request.POST.get("communication_address", client_user.communication_address),

                # register
                "reg_postal_code" : request.POST.get("reg_postal_code", client_user.reg_postal_code),
                "reg_country" : request.POST.get("reg_country", client_user.reg_country),
                "reg_state" : request.POST.get("reg_state", client_user.reg_state),
                "reg_city" : request.POST.get("reg_city", client_user.reg_city),
                "reg_address" : request.POST.get("reg_address", client_user.reg_address),

                # warehouse
                "warehouse_postal_code": request.POST.get("warehouse_postal_code", client_user.warehouse_postal_code),
                "warehouse_country": request.POST.get("warehouse_country", client_user.warehouse_country),
                "warehouse_state": request.POST.get("warehouse_state", client_user.warehouse_state),
                "warehouse_city": request.POST.get("warehouse_city", client_user.warehouse_city),
                "warehouse_address": request.POST.get("warehouse_address", client_user.warehouse_address),

                # warehouse
                "outlet_address": request.POST.get("outlet_address", client_user.outlet_address),
                "outlet_city": request.POST.get("outlet_city", client_user.outlet_city),
                "outlet_state": request.POST.get("outlet_state", client_user.outlet_state),
                "outlet_country": request.POST.get("outlet_country", client_user.outlet_country),
                "outlet_postal_code": request.POST.get("outlet_postal_code", client_user.outlet_postal_code)
            }

            # If any error occurred, render the form again with error messages
            return render(
                request,
                "useraccount/edit_client.html",
                {
                    "email_error": email_error,
                    "primary_contact_person_error": primary_contact_person_error,
                    # "warehouse_address_error": warehouse_address_error,
                    "upload_gst_error": upload_gst_error,
                    "mobile_error": mobile_error,
                    "company_name_error": company_name_error,
                    # "website_link_error": website_link_error,
                    "industry_type_error": industry_type_error,
                    "upload_pan_error": upload_pan_error,
                    "designation_error": designation_error,
                    "pancard_number_error": pancard_number_error,
                    "gst_no_error": gst_no_error,
                    "reg_address_error":reg_address_error,
                    "communication_address_error":communication_address_error,
                    "date_of_establishment_error":date_of_establishment_error,
                    "client_user_edit": client_user_edit,
                },
            )
        else:
            # Save the user and client_user objects
            user.save()
            client_user.save()

            # RequestBussinessRegister Update model data
            print("phone hidden",request.POST.get("mobile_no_hidden"))
            print("Phone is:", request.POST.get("mobile_no"))
            print("Email is :", request.POST.get("email"))
            print("Email hidden:", request.POST.get("email_hidden"))

            request_user = RequestBussinessRegister.objects.get(
                email=request.POST.get("email_hidden"),
                mobile_number=request.POST.get("mobile_no_hidden"),
            )

            logger.debug(request_user)

            # request_user.primary_contact_person = request.POST.get(
            #     "primary_contact_person"
            # )
            # request_user.designation = request.POST.get("designation")
            # request_user.email = request.POST.get("email")
            # request_user.mobile_number = request.POST.get("mobile_no")
            # request_user.bussiness_name = request.POST.get("company_name")

            # request_user.save()
            new_email = request.POST.get("email")
            new_mobile_no = request.POST.get("mobile_no")
            primary_contact_person = request.POST.get("primary_contact_person")
            designation = request.POST.get("designation")
            bussiness_name = request.POST.get("company_name")

            # Validation checks
            email_error = ""
            mobile_error = ""

            # Check if the new email is already in use by another instance
            if not new_email:
                email_error = "Email is required."
            # elif RequestBussinessRegister.objects.filter(email=new_email).exclude(pk=request_user.pk).exists():
            #     email_error = "This email is already in use. Please use a different email address."

            # Check if the new mobile number is already in use by another instance
            if not new_mobile_no:
                mobile_error = "Mobile number is required."
            # elif RequestBussinessRegister.objects.filter(mobile_number=new_mobile_no).exclude(pk=request_user.pk).exists():
            #     print("here mobile 3")
            #     mobile_error = "This mobile number is already in use. Please use a different mobile number."
            #     print(mobile_error)

            if email_error or mobile_error:
                print(mobile_error)
                # If there are errors, you can return or render the template with error messages
                return render(  request,
                "useraccount/edit_client.html", {
                    "request_user": request_user,
                    "email_error": email_error,
                    "mobile_error": mobile_error,
                    "client_user":client_user

                })
            else:
                # No validation errors, so update and save
                request_user.primary_contact_person = primary_contact_person
                request_user.designation = designation
                request_user.email = new_email
                request_user.mobile_number = new_mobile_no
                request_user.bussiness_name = bussiness_name

                try:
                    request_user.save()
                    print("RequestBussinessRegister updated successfully")
                except ValidationError as e:
                    print(f"Error saving RequestBussinessRegister: {e}")

            # OnboardingGstVerify Update model data

            gst_verify_data = OnboardingGstVerify.objects.get(
                request_user=request_user.id
            )
            gst_verify_data.request_user = request_user
            # gst_verify_data.gst_number = request.POST.get("gst_no")
            # gst_verify_data.first_address = request.POST.get("address_line1")
            # gst_verify_data.second_address = request.POST.get("address_line2")
            # gst_verify_data.postal_code = request.POST.get("pin_code")
            # gst_verify_data.city = request.POST.get("city")
            # gst_verify_data.state = request.POST.get("state")
            # gst_verify_data.country = request.POST.get("country")
            print("date of establishment is :", request.POST.get("date_of_establishment"))
            gst_verify_data.date_of_establishment = request.POST.get("date_of_establishment")
            gst_verify_data.pancard_no = request.POST.get("pancard_no")

            gst_verify_data.save()

            # OnboardingBussinessDetails Update model data
            bussiness_data_verify = OnboardingBussinessDetails.objects.get(
                onboarding_gst_verify=gst_verify_data.id
            )
            bussiness_data_verify.onboarding_gst_verify = gst_verify_data
            bussiness_data_verify.first_company_type = request.POST.get(
                "first_company_type"
            )
            bussiness_data_verify.industry_type = request.POST.get("industry_type")
            bussiness_data_verify.website_link = request.POST.get("website_link")

            bussiness_data_verify.save()

            print("bank assing id is :", bussiness_data_verify.id)

            # OnboardingBankDetails Update model data
            try:
                bank_update_data = OnboardingBankDetails.objects.get(
                    onboarding_bussiness_details=bussiness_data_verify.id
                )
                bank_update_data.onboarding_bussiness_details = bussiness_data_verify
            except OnboardingBankDetails.DoesNotExist:
                bank_update_data = OnboardingBankDetails.objects.create(
                    onboarding_bussiness_details=bussiness_data_verify,
                )

            # Update fields only if the file is uploaded
            if request.FILES.get("upload_pan"):
                bank_update_data.upload_pan = request.FILES.get("upload_pan")

            if request.FILES.get("upload_gst"):
                bank_update_data.upload_gst = request.FILES.get("upload_gst")

            if request.FILES.get("certificate_of_corporation"):
                bank_update_data.certificate_of_corporation = request.FILES.get("certificate_of_corporation")

            if request.FILES.get("msme"):
                bank_update_data.msme = request.FILES.get("msme")

            if request.FILES.get("authorization_letter"):
                bank_update_data.authorization_letter = request.FILES.get("authorization_letter")

            if request.FILES.get("adhaar"):
                bank_update_data.aadhar = request.FILES.get("adhaar")

            # Save the bank_update_data instance
            bank_update_data.save()

            # Onboarding Communication
            try:
                onboarding_OnboardingCommunication = OnboardingCommunication.objects.get(onboarding_bank_details=bank_update_data.id)
                onboarding_OnboardingCommunication.onboarding_bank_details = bank_update_data
            except OnboardingCommunication.DoesNotExist:
                onboarding_OnboardingCommunication = OnboardingCommunication.objects.create(
                    onboarding_bank_details=bank_update_data,
                )

            onboarding_OnboardingCommunication.communication_postal_code = self.request.POST.get("communication_postal_code" , None)
            onboarding_OnboardingCommunication.communication_address = self.request.POST.get("communication_address" , None)
            onboarding_OnboardingCommunication.communication_city = self.request.POST.get("communication_city" , None)
            onboarding_OnboardingCommunication.communication_state = self.request.POST.get("communication_state" , None)
            onboarding_OnboardingCommunication.communication_country = self.request.POST.get("communication_country" , None)

            onboarding_OnboardingCommunication.save()

            # Onboarding Register
            try:
                onboarding_OnboardingRegisteredAddress = OnboardingRegisteredAddress.objects.get(onboarding_comm_details=onboarding_OnboardingCommunication.id)
                onboarding_OnboardingRegisteredAddress.onboarding_comm_details = onboarding_OnboardingCommunication
            except OnboardingRegisteredAddress.DoesNotExist:
                onboarding_OnboardingRegisteredAddress = OnboardingRegisteredAddress.objects.create(onboarding_comm_details=onboarding_OnboardingCommunication)

            onboarding_OnboardingRegisteredAddress.reg_postal_code = self.request.POST.get("reg_postal_code", None)
            onboarding_OnboardingRegisteredAddress.reg_address = self.request.POST.get("reg_address", None)
            onboarding_OnboardingRegisteredAddress.reg_city = self.request.POST.get("reg_city", None)
            onboarding_OnboardingRegisteredAddress.reg_state = self.request.POST.get("reg_state", None)
            onboarding_OnboardingRegisteredAddress.reg_country = self.request.POST.get("reg_country", None)

            onboarding_OnboardingRegisteredAddress.save()

            # Onboarding Warehouse
            try:
                onboarding_OnboardingWarehouse = WarehouseAddress.objects.get(onboarding_reg_details=onboarding_OnboardingRegisteredAddress.id)
                onboarding_OnboardingWarehouse.onboarding_reg_details = onboarding_OnboardingRegisteredAddress
            except WarehouseAddress.DoesNotExist:
                onboarding_OnboardingWarehouse = WarehouseAddress.objects.create(onboarding_reg_details=onboarding_OnboardingRegisteredAddress)

            onboarding_OnboardingWarehouse.warehouse_postal_code = self.request.POST.get("warehouse_postal_code", None)
            onboarding_OnboardingWarehouse.warehouse_country = self.request.POST.get("warehouse_country", None)
            onboarding_OnboardingWarehouse.warehouse_state = self.request.POST.get("warehouse_state", None)
            onboarding_OnboardingWarehouse.warehouse_city = self.request.POST.get("warehouse_city", None)
            onboarding_OnboardingWarehouse.warehouse_address = self.request.POST.get("warehouse_address", None)

            onboarding_OnboardingWarehouse.save()

            # Onboarding Outlet
            try:
                onboarding_OnboardingOutlet = OutletAddress.objects.get(onboarding_warehouse_details=onboarding_OnboardingWarehouse.id)
                onboarding_OnboardingOutlet.onboarding_warehouse_details = onboarding_OnboardingWarehouse
            except OutletAddress.DoesNotExist:
                onboarding_OnboardingOutlet = OutletAddress.objects.create(onboarding_warehouse_details=onboarding_OnboardingWarehouse)

            onboarding_OnboardingOutlet.outlet_postal_code = self.request.POST.get("outlet_postal_code", None)
            onboarding_OnboardingOutlet.outlet_country = self.request.POST.get("outlet_country", None)
            onboarding_OnboardingOutlet.outlet_state = self.request.POST.get("outlet_state", None)
            onboarding_OnboardingOutlet.outlet_city = self.request.POST.get("outlet_city", None)
            onboarding_OnboardingOutlet.outlet_address = self.request.POST.get("outlet_address", None)

            onboarding_OnboardingOutlet.save()


            messages.success(self.request,_(f'Client user "{client_user.user.email}" edited successfully'),)
            return redirect("client-list")  # Redirect to the client user list page or any other page as needed


class DeleteClientView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        client_details = get_object_or_404(ClientDetails, user=user)

        try:
            request_user = RequestBussinessRegister.objects.get(
                email=user.email, mobile_number=client_details.mobile_no
            )
        except RequestBussinessRegister.DoesNotExist:
            request_user = None

        try:
            email_verify_table = ClientEmailVerify.objects.get(email=user.email)
        except ClientEmailVerify.DoesNotExist:
            email_verify_table = None

        try:
            user_profile_table = UserProfile.objects.get(
                mobile_number=client_details.mobile_no
            )
        except UserProfile.DoesNotExist:
            user_profile_table = None

        # Delete the associated ClientDetails and User objects
        if email_verify_table:
            email_verify_table.delete()

        if user_profile_table:
            user_profile_table.delete()

        if request_user:
            request_user.delete()

        client_details.delete()
        user.delete()

        messages.success(request, f'Client user "{user.email}" deleted successfully')
        return redirect("client-list")


# userinfoAPIDRF
class UserInfoAPIview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        print("user:", user)
        try:
            client_details = ClientDetails.objects.get(user=user)
            serializer = ClientDetailsSerializer(client_details)
            return Response(
                {"ClientDetails": serializer.data}, status=status.HTTP_200_OK
            )
        except ClientDetails.DoesNotExist:
            try:
                voucher_user = VoucherUser.objects.get(user=user)
                serializer = VoucherUsertDetailsSerializer(voucher_user)
            except Exception as e:
                voucher_user = VoucherUser.objects.create(user=user,mobile_no=user.username)
                serializer = VoucherUsertDetailsSerializer(voucher_user)

            return Response(
                {"ClientDetails": serializer.data}, status=status.HTTP_200_OK
            )

    def put(self, request, *args, **kwargs):

        user = self.request.user
        data = request.data
        print(data, user.__dict__)
        try:
            client_details = ClientDetails.objects.get(user=user)
            print(client_details, "adda")
            serializer = ClientDetailsSerializer(
                client_details, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"ClientDetails": serializer.data}, status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ClientDetails.DoesNotExist:
            try:
                voucher_user_obj = VoucherUser.objects.get(user=user)
            except VoucherUser.DoesNotExist:
                voucher_user_obj = VoucherUser.objects.create(user=user)

            mobile_no = request.data.get("mobile_no")
            if ClientDetails.objects.filter(mobile_no=mobile_no).exists():
                return Response({"message":"user already exist with this mobile no"},status=status.HTTP_400_BAD_REQUEST)
            if VoucherUser.objects.filter(mobile_no=mobile_no).exists():
                return Response({"message":"user already exist with this mobile no"},status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(username=mobile_no).exists():
                return Response({"message":"user already exist with this mobile no"},status=status.HTTP_400_BAD_REQUEST)                

            voucher_user_serializer = VoucherUsertDetailsSerializer(
                voucher_user_obj, data=request.data, partial=True
            )

            if voucher_user_serializer.is_valid():
                voucher_user_serializer.save()
            print(voucher_user_serializer.data, "weolco")
            return Response(
                {
                    "data": "client details created ",
                    "user": voucher_user_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )


class AdminUserListView(View):
    def get(self, request):
        admin_list = User.objects.filter(is_staff=True, is_superuser=False).order_by(
            "-date_joined"
        )

        context = {
            "admin_list": admin_list,
        }
        return render(request, "useraccount/admin_list.html", context)


from role_permission.models import Roles


class AdminUser(View):
    def get(self, request):
        gst_list = User.objects.filter(groups__name="admin")
        roles = Role.objects.all()
        
        

        context = {
            "gst_list": gst_list,
            "all_role":roles
        }

        return render(request, "useraccount/adminuser.html", context)


    def post(self, request, **extra_fields):
        first_name = self.request.POST.get("first_name")
        last_name = self.request.POST.get("last_name")
        email = self.request.POST.get("email")

        role_id = request.POST.get("role")
        if role_id is None or len(role_id) <= 0:
            messages.error("role is required")
            return redirect("AdminUser")

        

        email_error = ""
        if not email:
            email_error = "Email is required."
        elif not is_valid_email(email):
            email_error = "Please enter a valid email address."

        first_name_error = ""
        if not first_name:
            first_name_error = "First Name is required and can only contain letters."

        last_name_error = ""
        if not last_name:
            last_name_error = "Last Name is required and can only contain letters."
        # elif not is_valid_text(last_name):
        #     last_name_error = 'Last Name can only contain letters.'

        if email_error or first_name_error or last_name_error:
            # If any error occurred, render the form again with error messages
            return render(
                request,
                "useraccount/adminuser.html",
                {
                    "email_error": email_error,
                    "first_name_error": first_name_error,
                    "last_name_error": last_name_error,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
        else:

            if first_name and last_name and email:

                is_user_exists = User.objects.filter(email=email).exists()
                static_pass = "admin@123"
                if not is_user_exists:
                    extra_fields.setdefault("is_staff", True)

                    user = User.objects.create(
                        username=email,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        password=make_password(static_pass),
                        **extra_fields,
                    )
                    user_group = Group.objects.get(name="admin")
                    user.groups.add(user_group)
                    roles_obj = Roles(user=user)
                    role_obj = Role.objects.get(id=role_id)
                    roles_obj.role = role_obj
                    roles_obj.save()
                    messages.success(request, "Admin saved successfully")
                else:
                    messages.error(request, "User Already Exists")
            else:
                messages.error(request, "All fields are required")
            return redirect("AdminUser")


from role_permission.models import Roles,Role


class EditAdminView(View):
    template_name = "useraccount/edit_admin.html"

    def get(self, request, pk):
        admin_user = User.objects.get(pk=pk)
        roles = Role.objects.all()
        user_role = Roles.objects.get(user=admin_user)
        current_role = user_role.role

        logger.debug(current_role)


        return render(
            request,
            self.template_name,
            {
                "admin_user": admin_user,
                "all_role": roles,
                "current_role":current_role
               
            },
        )

    def post(self, request, pk):
        
        id_role = request.POST.get("role")
        admin_user = User.objects.get(pk=pk)

        admin_user.email = request.POST.get("email")
        admin_user.first_name = request.POST.get("first_name")
        admin_user.last_name = request.POST.get("last_name")
        admin_user.date_joined = timezone.now()
        try:
            roles_obj = Roles.objects.get(user=admin_user)
        except Roles.DoesNotExist:
            roles_obj = Roles.objects.create(user=admin_user)

        role_obj = Role.objects.get(id=id_role) 
        roles_obj.role = role_obj
        roles_obj.save()

        email_error = ""
        if not admin_user.email:
            email_error = "Email is required."
        elif not is_valid_email(admin_user.email):
            email_error = "Please enter a valid email address."

        first_name_error = ""
        if not admin_user.first_name:
            first_name_error = "First Name is required and can only contain letters."
        # elif not is_valid_text(admin_user.first_name):
        #     first_name_error = 'First Name can only contain letters.'

        last_name_error = ""
        if not admin_user.last_name:
            last_name_error = "Last Name is required and can only contain letters."
        # elif not is_valid_text(admin_user.last_name):
        #     last_name_error = 'Last Name can only contain letters.'

        if email_error or first_name_error or last_name_error:
            # If any error occurred, render the form again with error messages
            return render(
                request,
                "useraccount/edit_admin.html",
                {
                    "email_error": email_error,
                    "first_name_error": first_name_error,
                    "last_name_error": last_name_error,
                    "email": admin_user.email,
                    "first_name": admin_user.first_name,
                    "last_name": admin_user.last_name,
                },
            )
        else:
            admin_user.save()
            messages.success(
                request, _(f'Client user "{admin_user.email}" edit successfully')
            )
        return redirect(
            "admin-list"
        )  # Redirect to the client user list page or any other page as needed


class DeleteAdminView(View):
    def get(self, request, pk):
        admin_user = User.objects.get(pk=pk)
        admin_user.delete()
        messages.success(
            request, f'Admin user "{admin_user.email}" deleted successfully'
        )
        return redirect("admin-list")


# user datils API------
from django.views.generic import ListView
from django.db.models import Q
from django.views.generic.edit import UpdateView
from .models import UniqueStrings
import logging

logger = logging.getLogger(__name__)


# login api-----------------
class LoginView(APIView):

    def post(self, request, *args, **kwargs):

        email = request.data.get("email")
        password = request.data.get("password")
        login_type = request.data.get("logintype")

        if login_type in ["client", "customer"]:
            if email == "" or email is None:
                return Response(
                    {"message": "Please provide email"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if password == "" or password is None:
                return Response(
                    {"message": "Please Provide password for login"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_string = UniqueStrings.objects.filter(unique_string=email)
            logger.debug(user_string)
            logger.debug(f"its me pranav{email}")

            if User.objects.filter(email=email).exists() or user_string.exists():
                if User.objects.filter(email=email).exists():
                    user = User.objects.filter(email=email).first()
                else:
                    user_string_obj = user_string.first()
                    user = user_string_obj.user
                
                logger.debug(user)
                if not user.check_password(password):
                    return Response(
                        {"msg": "Incorrect Email or password", "flag": False},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                user_id = user.id

                user_groups = list(user.groups.values_list("name", flat=True))
                user.is_verified = True
                user.save()
                try:
                    client_obj = ClientDetails.objects.get(user=user)
                    client_id_unique_obj = UniqueStrings.objects.get(user=user)
                    client_id_unique = client_id_unique_obj.unique_string
                    company_name = client_obj.company_name
                except Exception as e:
                    return Response({"msg": "Client Doesn't exist", "flag": False},
                        status=status.HTTP_400_BAD_REQUEST,)
                if user.is_verified:
                    login(request, user)

                    refresh = RefreshToken.for_user(user)

                    user_auth_token_obj = UserAuthTokens.objects.filter(user_info=user)

                    if user_auth_token_obj.exists():
                        user_auth_token_obj.update(
                            access_token=refresh.access_token, refresh_token=refresh
                        )
                    else:
                        UserAuthTokens.objects.create(
                            user_info=user,
                            access_token=refresh.access_token,
                            refresh_token=refresh,
                        )
                        # user_v = VocherLoginConnect.objects.get(voucher=request.data.get("voucher_code"))

                    return Response(
                        {
                            "msg": "User login",
                            "id": user_id,
                            "user": user_groups,
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                            "client_id":client_id_unique,
                            "company_name":company_name
                        },
                        status=status.HTTP_200_OK,
                    )

            else:
                return Response(
                    {"msg": "Incorrect Email or password", "flag": False},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"msg": "Invalid User", "flag": False},
                status=status.HTTP_400_BAD_REQUEST,
            )


# voucher code verify api -----
from oscar.apps.voucher.models import Voucher
from oscar.apps.voucher.models import VoucherSet
from datetime import date
from bannermanagement.models import VoucherSet as Vo


class vouchercodeverify(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = VoucherSerializer(data=data)
        if serializer.is_valid():
            code = serializer.validated_data["code"]
            today = date.today()
            vocher_check = Voucher.objects.filter(
                code=code,
                voucher_set__start_datetime__lte=today,
                voucher_set__end_datetime__gte=today,
            )
            vocher_check1 = Voucher.objects.get(code=code)
            try:
                voucher_custom_set = Vo.objects.filter(
                    voucher=vocher_check1.voucher_set
                )
            except Exception as e:
                logger.error(e)
                import traceback

                f = traceback.format_exc()
                logger.error(f" error in login {f=}")
            if vocher_check1.num_orders > 0:
                return Response(
                    {"succes": False, "message": "already used voucher"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if vocher_check.exists() and voucher_custom_set.exists():
                # try:
                #     voucher_details = VocherLoginConnect.objects.get(voucher = voucher_details.first())
                # except VocherLoginConnect.DoesNotExist:
                #     voucher_details = VocherLoginConnect.objects.create(voucher=voucher_details.first())
                return Response(
                    {
                        "message": "voucher is valid",
                        "description": vocher_check1.voucher_set.description,
                    }
                )
            else:
                if Voucher.objects.filter(
                    code=code,
                ).exists():
                    return Response({"message": "voucher expired"})
                return Response({"message": "voucher is not valid"})

        else:
            return Response({"message": "serializer is not valid"})


class GetALLVoucherCode(APIView):
    def get(self, request, *args, **kwargs):
        obj = Voucher.objects.filter().values("name", "code")
        return Response({"voucher_code": obj})


import random
from .sms import SmsOtpIntegration


def send_otp_to_phone(mobile_number, otp):
    try:

        url = f"https://2factor.in/API/V1/{settings.API_KEY}/SMS/{mobile_number}/{otp}"
        response = requests.get(url)
        return otp
    except Exception as e:
        return None


from random import randint


class SentOtpForMobile(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        
        serializer = EmailSentSerializer(data=data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            try:
                mob_obj = UserProfile.objects.get(mobile_number=mobile_number)
            except Exception as e:
                mob_obj = UserProfile.objects.create(mobile_number=mobile_number)

            try:
                mob_obj_2 = ClientDetails.objects.filter(mobile_no=mob_obj.mobile_number).exists()

                user_exists = User.objects.filter(username=mob_obj.mobile_number).exists()
                email_exists_in_business = RequestBussinessRegister.objects.filter(mobile_number=mob_obj.mobile_number).exists()
                email_exists_in_business_two = RequestBussinessRegister.objects.filter(mobile_number=f"+91{mob_obj.mobile_number}").exists()


                
      

            except Exception as e:
                mob_obj_2 = None
                user_exists = None
                email_exists_in_business = None
                email_exists_in_business_two = None

            # if not mob_obj_2:
            if not mob_obj_2 and not user_exists and not email_exists_in_business and not email_exists_in_business_two:

                if mob_obj:
                    otp = randint(1000, 9999)
                    mob_obj.otp = otp
                    mob_obj.save()
                    SmsOtpIntegration.send_otp_sms(mobile_number, otp, "customer")
                    return Response({"message": "Otp sent on your mobile number"})
                else:
                    otp = randint(1000, 9999)

                    UserProfile.objects.create(mobile_number=mobile_number, otp=otp)

                    SmsOtpIntegration.send_otp_sms(mobile_number, otp, "customer")

                    return Response({"message": "Otp sent on your mobile number"})
            else:

                return Response(
                    {"message": "Your Mobile Number is already exists in client side."}
                )

        else:
            return Response({"message": "serializer is not valid"})


# new api for login customer--------------------------------------------------
class CustomerLoginView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = LoginSerializer(data=data)
        if serializer.is_valid():
            otp = serializer.validated_data["otp"]
            mobile_number = serializer.validated_data["mobile_number"]

            user_obje = User.objects.filter(username=mobile_number)
            if user_obje.exists():
                user_check = UserProfile.objects.filter(
                    mobile_number=mobile_number, otp=otp
                )

                if user_check.exists():

                    user = User.objects.get(username=mobile_number)

                    print("voucher")
                    voucher_data = check_voucher_code(request.data.get("voucher"))
                    if voucher_data[0]:
                        return Response(
                            {"detail": voucher_data[1]}, status=status.HTTP_200_OK
                        )
                    if user:

                        try:
                            voucher_details = VocherLoginConnect.objects.get(
                                user=user, voucher__code=request.data.get("voucher")
                            )
                            if voucher_details.count == 3:
                                return Response({"detail": "already signed in 3 times"})
                            voucher_details.count = voucher_details.count + 1
                            voucher_details.save()
                        except VocherLoginConnect.DoesNotExist:
                            voucher_details = VocherLoginConnect.objects.create(
                                user=user, voucher=voucher_data[1], count=1
                            )
                        login(request, user)

                        refresh = RefreshToken.for_user(user)

                        user_auth_token_obj = UserAuthTokens.objects.filter(
                            user_info=user
                        )

                        if user_auth_token_obj.exists():
                            user_auth_token_obj.update(
                                access_token=refresh.access_token, refresh_token=refresh
                            )
                        else:
                            UserAuthTokens.objects.create(
                                user_info=user,
                                access_token=refresh.access_token,
                                refresh_token=refresh,
                            )

                        try:
                            basket = Basket.objects.get(owner=user, status="Open")
                            basket.vouchers.clear()

                        except:
                            pass

                        return Response(
                            {
                                # "msg": "User login",
                                "user_id": user.id,
                                "msg": "Voucher login",
                                "login_left": int(3) - voucher_details.count,
                                "description": voucher_details.voucher.voucher_set.description,
                                "refresh": str(refresh),
                                "access": str(refresh.access_token),
                            },
                            status=status.HTTP_200_OK,
                        )

                    else:
                        return Response(
                            {"msg": "Please check your mobile number", "flag": False},
                            status=status.HTTP_200_OK,
                        )
                else:
                    return Response(
                        {"msg": "Wrong OTP! Please check your otp", "flag": False},
                        status=status.HTTP_200_OK,
                    )

            else:
                otp_obj = UserProfile.objects.filter(
                    mobile_number=mobile_number, otp_verify=True
                )
                if otp_obj.exists():
                    User.objects.create(username=mobile_number)
                    user = User.objects.get(username=mobile_number)
                    user_group = Group.objects.get(name="customer")
                    user.groups.add(user_group)

                    user_checkk = UserProfile.objects.filter(
                        mobile_number=mobile_number, otp=otp
                    )
                    if user_checkk.exists():

                        user = User.objects.get(username=mobile_number)

                        voucher_data = check_voucher_code(request.data.get("voucher"))
                        if voucher_data[0]:
                            return Response(
                                {"detail": voucher_data[1]}, status=status.HTTP_200_OK
                            )
                        if user:

                            try:
                                voucher_details = VocherLoginConnect.objects.get(
                                    user=user, voucher__code=request.data.get("voucher")
                                )
                                if voucher_details.count == 3:
                                    return Response(
                                        {"detail": "already signed in 3 times"}
                                    )
                                voucher_details.count = voucher_details.count + 1
                                voucher_details.save()
                            except VocherLoginConnect.DoesNotExist:
                                voucher_details = VocherLoginConnect.objects.create(
                                    user=user, voucher=voucher_data[1], count=1
                                )

                            login(request, user)

                            refresh = RefreshToken.for_user(user)

                            user_auth_token_obj = UserAuthTokens.objects.filter(
                                user_info=user
                            )

                            if user_auth_token_obj.exists():
                                user_auth_token_obj.update(
                                    access_token=refresh.access_token,
                                    refresh_token=refresh,
                                )
                            else:
                                UserAuthTokens.objects.create(
                                    user_info=user,
                                    access_token=refresh.access_token,
                                    refresh_token=refresh,
                                )
                            try:
                                basket = Basket.objects.get(owner=user, status="Open")
                                basket.vouchers.clear()

                            except:

                                pass

                            return Response(
                                {
                                    # "msg": "User login",
                                    "user_id": user.id,
                                    "msg": "Voucher login",
                                    "refresh": str(refresh),
                                    "login_left": int(3) - voucher_details.count,
                                    "description": voucher_details.voucher.voucher_set.description,
                                    "access": str(refresh.access_token),
                                },
                                status=status.HTTP_200_OK,
                            )

                        else:
                            return Response(
                                {
                                    "msg": "Please check your mobile number",
                                    "flag": False,
                                },
                                status=status.HTTP_200_OK,
                            )
                    else:
                        return Response(
                            {"msg": "Wrong OTP! Please check your otp", "flag": False},
                            status=status.HTTP_200_OK,
                        )

                else:
                    return Response(
                        {"msg": "your mobile number does not exists", "flag": False},
                        status=status.HTTP_200_OK,
                    )

        else:
            return Response(
                {"msg": "Something went wrong", "flag": False},
                status=status.HTTP_404_NOT_FOUND,
            )


class VerifyRegistrations(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = VarifyRegistrationSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        mobile_number = serializer.validated_data["mobile_number"]
        otp = serializer.validated_data["otp"]

        usrprofile_obj = UserProfile.objects.filter(
            mobile_number=mobile_number, otp=otp
        )
        if usrprofile_obj.exists():
            usrprofile_obj.update(otp_verify=True)
            return Response({"status": 200, "message": "otp verify"})
        else:
            usrprofile_obj.update(otp_verify=False)
            return Response({"message": "otp not verify"})


from django.utils import timezone


class GetVouchersView(APIView):
    def get(self, request):
        now = timezone.now()
        new_data = Voucher.objects.filter()
        if new_data:

            list_data = []
            for j in new_data:
                dict_data = {}
                dict_data["id"] = j.id
                dict_data["name"] = j.name
                dict_data["code"] = j.code
                dict_data["start_datetime"] = j.start_datetime
                dict_data["end_datetime"] = j.end_datetime
                dict_data["total_discount"] = j.total_discount

                voucher_offers = j.offers.all()
                for k in voucher_offers:
                    dict_data["voucher_value"] = k.benefit.value
                list_data.append(dict_data)
            return Response({"data": list_data})
        else:
            return Response({"data": "voucher not exists at this moments"})


from oneup_project.settings import React_API_URl,REACT_URL


class ForgotPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        email_serializer = PasswordEmailSerializer(data=request.data)

        if email_serializer.is_valid():
            email = email_serializer.validated_data["email"]
            user = User.objects.filter(email=email).first()

            if user:
                # Generate Pin Code and store it in the database
                otp_instance = generate_OTP(user)
                # Construct the password reset link using reverse
                user_id_forget = user.id
                reset_link = REACT_URL +"verify-otp/"+ f"user-id={user_id_forget}/"

                # Send the Password Reset Email with OTP
                subject = "Send OTP"
                html_message = f" To log in to your  account use OneUpBrand One Time Password : {otp_instance.otp} and Page Link : {reset_link} Make sure you do not share it with anyone for security reasons"
                plain_message = strip_tags(html_message)
                from_email = settings.EMAIL_HOST_USER
                to_email = [email]

                send_mail(
                    subject,
                    plain_message,
                    from_email,
                    to_email,
                    html_message=html_message,
                )
                return Response(
                    {
                        "detail": "Password reset instructions have been sent to your email address."
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"detail": "Invalid Email."}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(email_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from oneup_project.settings import REACT_URL

class ForgotPasswordViewByCustomer(View):
    def post(self, request, pk, *args, **kwargs):
        try:
            user = User.objects.get(pk=pk)
            email = user.email

            # Generate Pin Code and store it in the database
            otp_instance = generate_OTP(user)
            # Construct the password reset link using reverse
            reset_link = f"{REACT_URL}verify-otp/user-id={user.id}/"

            # Send the Password Reset Email with OTP
            subject = "Send OTP"
            html_message = f" OTP is : {otp_instance.otp} and Page Link : {reset_link}"
            plain_message = strip_tags(html_message)
            from_email = settings.EMAIL_HOST_USER
            to_email = [email]

            send_mail(
                subject, plain_message, from_email, to_email, html_message=html_message
            )

            messages.success(
                request,
                "Password reset instructions have been sent to your email address.",
            )
            return reverse("dashboard:user-detail", pk)
        except User.DoesNotExist:
            messages.error(request, "Customer not found.")
            return reverse("dashboard:user-detail", pk)
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            messages.error(request, "Something Went Wrong.")
            return reverse("dashboard:user-detail", pk)


class OTPVerifyView(APIView):
    def post(self, request, pk):
        user = get_object_or_404(User, id=pk)
        entered_OTP_serializer = VerifyOTPSerializer(data=request.data)

        if entered_OTP_serializer.is_valid():
            entered_OTP = entered_OTP_serializer.validated_data["OTP"]
            latest_otp = OTP.objects.filter(user=user).first()

            if latest_otp and latest_otp.otp == entered_OTP:
                latest_otp.verified = True
                latest_otp.save()
                return JsonResponse({"verified": True})
            else:
                return JsonResponse(
                    {"verified": False}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return JsonResponse(
                entered_OTP_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )


def generate_OTP(user, length=6):
    """Generate a random OTP."""
    characters = string.digits
    otp_generated = "".join(secrets.choice(characters) for _ in range(length))
    # Check if there's an existing OTP for the user
    try:
        existing_otp = OTP.objects.get(user=user)
        # If an OTP already exists, update its value
        existing_otp.otp = otp_generated
        existing_otp.save()
    except ObjectDoesNotExist:
        # If no OTP exists, create a new one
        existing_otp = OTP.objects.create(user=user, otp=otp_generated)

    return existing_otp


class ResetPasswordView(APIView):
    def post(self, request, pk):
        serializers_data = ResetPasswordSerializer(data=request.data)

        if serializers_data.is_valid():
            password = serializers_data.validated_data["password"]
            confirm_password = serializers_data.validated_data["confirm_password"]

            user = get_object_or_404(User, id=pk)
            otp_instance = get_object_or_404(OTP, user=user)

            if password == confirm_password:
                user = otp_instance.user
                user.set_password(password)
                user.save()

                return Response({"Password updated successfully!"})
            else:
                return Response({"Passwords do not match!"})
        else:
            return Response(serializers_data.errors, status=status.HTTP_400_BAD_REQUEST)


from .models import Contact
from .serializers import ContactSerializer


class ContactUsAPIView(generics.CreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class ContactListView(View):
    template_name = "useraccount/contact_list.html"

    def get(self, request):
        contacts_list = Contact.objects.all()
        return render(request, self.template_name, {"contacts_list": contacts_list})

    def post(self, request):
        email = request.POST.get("email")
        searched_email = email

        if email:
            contacts_list = Contact.objects.filter(email__icontains=email)
        else:
            contacts_list = Contact.objects.all()
        return render(
            request,
            self.template_name,
            {"contacts_list": contacts_list, "searched_email": searched_email},
        )


def is_valid_email(email):
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(email_regex, email))


def is_valid_text(text):
    text_regex = r"^[A-Za-z]+$"
    return bool(re.match(text_regex, text))


def is_valid_mobile_number(mobile_number):
    mobile_regex = r"^\d{10}$"
    return bool(re.match(mobile_regex, mobile_number))


def is_valid_pin_code(pin_code):
    pin_code_regex = r"^\d{6}$"
    return bool(re.match(pin_code_regex, pin_code))


class VerifyOTPForOrder(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = VarifyRegistrationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        mobile_number = serializer.validated_data["mobile_number"]
        otp = serializer.validated_data["otp"]
        usrprofile_obj = UserProfile.objects.filter(
            mobile_number=mobile_number, otp=otp
        )
        if usrprofile_obj.exists():
            user_details = usrprofile_obj.first()
            user = User.objects.get(username=user_details.mobile_number)
            # order_details = order_model.objects.filter(user=user)
            data = (
                order_model.objects.filter(user=user)
                .annotate(product_count=Count("basket__lines"))
                .values(
                    "product_count",
                    "number",
                    "date_placed",
                    "status",
                    "total_incl_tax",
                    "payment_types",
                )
                .order_by("-date_placed")
            )
            return Response({"data": data}, status=status.HTTP_200_OK)
        else:
            usrprofile_obj.update(otp_verify=False)
            return Response({"message": "otp not verify"})


class SentOtpForMobileTrackOrder(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = EmailSentSerializer(data=data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            mob_obj = UserProfile.objects.filter(mobile_number=mobile_number)
            if mob_obj.exists():
                otp = randint(1000, 9999)
                mob_obj.update(otp=otp)
                SmsOtpIntegration.send_otp_sms_trackorder(
                    mobile_number, otp, "customer"
                )
                return Response({"message": "Otp sent on your mobile number"})
            else:
                return Response(
                    {"error": "mobile number not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        else:
            return Response({"message": "enter valid  number"})


voucher_model = get_model("voucher", "Voucher")


class VoucherCheck(APIView):
    def post(self, request):
        code = request.data.get("code")
        voucher = voucher_model.objects.get(code=code)

        if voucher.num_orders == 0:
            return Response({"data": "Voucher usable"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"data": "Voucher not usable"}, status=status.HTTP_406_NOT_ACCEPTABLE
            )


class UserAlreadyExistsSignup(APIView):
    def post(self, request, *args, **kwargs):
        serializer_data = SignupCheckingSerializer(data=request.data)

        email_status = None
        mobile_status = None
        if serializer_data.is_valid():
            # Check if the mobile number exists and its status
            mobile_number = UserProfile.objects.filter(
                mobile_number=serializer_data.validated_data["mobile_number"]
            ).first()
            if mobile_number:
                if mobile_number.otp_verify:
                    mobile_status = "exists_otp"
                else:
                    mobile_status = "not_verified"
            else:
                mobile_status = "not_exists"

            # Check if the email exists and its status
            email_data = ClientEmailVerify.objects.filter(
                email=serializer_data.validated_data["email"]
            ).first()
            if email_data:
                if email_data.verified:
                    email_status = "exists_otp"
                else:
                    email_status = "not_verified"
            else:
                email_status = "not_exists"

            # Check ClientDetails table if both email and mobile number do not exist
            if mobile_status == "not_exists" and email_status == "not_exists":
                try:
                    client_detail_exists = ClientDetails.objects.get(
                        user__email=serializer_data.validated_data["email"],
                        mobile_no=serializer_data.validated_data["mobile_number"],
                    )
                    if client_detail_exists:
                        return Response(
                            {
                                "email": "exists_client_table",
                                "mobile": "exists_client_table",
                            },
                            status=status.HTTP_406_NOT_ACCEPTABLE,
                        )
                except ClientDetails.DoesNotExist:
                    return Response(
                        {"email": "not_exists", "mobile": "not_exists"},
                        status=status.HTTP_200_OK,
                    )

            # Response with the statuses of email and mobile number
            elif mobile_status == "exists_otp" and email_status == "exists_otp":
                try:
                    get_data = RequestBussinessRegister.objects.get(
                        email=email_data.email,
                        mobile_number=mobile_number.mobile_number,
                    )
                    try:
                        client_detail_exists = ClientDetails.objects.get(
                            user__email=serializer_data.validated_data["email"],
                            mobile_no=serializer_data.validated_data["mobile_number"],
                        )
                        if client_detail_exists:
                            return Response(
                                {
                                    "email": "exists_client_table",
                                    "mobile": "exists_client_table",
                                },
                                status=status.HTTP_406_NOT_ACCEPTABLE,
                            )
                    except ClientDetails.DoesNotExist:
                        request_data = {
                            "id": get_data.pk,
                            "primary_contact_person": get_data.primary_contact_person,
                            "designation": get_data.designation,
                            "email": get_data.email,
                            "mobile_number": get_data.mobile_number,
                        }
                        return Response(
                            {
                                "data": request_data,
                                "email": "exists_signup",
                                "mobile": "exists_signup",
                            },
                            status=status.HTTP_406_NOT_ACCEPTABLE,
                        )
                except RequestBussinessRegister.DoesNotExist:
                    try:
                        client_detail_exists = ClientDetails.objects.get(
                            user__email=serializer_data.validated_data["email"],
                            mobile_no=serializer_data.validated_data["mobile_number"],
                        )
                        if client_detail_exists:
                            return Response(
                                {
                                    "email": "exists_client_table",
                                    "mobile": "exists_client_table",
                                },
                                status=status.HTTP_406_NOT_ACCEPTABLE,
                            )
                        else:
                            return Response(
                                {
                                    "email": "not_exists_signup",
                                    "mobile": "not_exists_signup",
                                },
                                status=status.HTTP_404_NOT_FOUND,
                            )
                    except ClientDetails.DoesNotExist:
                        return Response(
                            {
                                "email": "not_exists_signup",
                                "mobile": "not_exists_signup",
                            },
                            status=status.HTTP_404_NOT_FOUND,
                        )

            return Response(
                {"email": email_status, "mobile": mobile_status},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": serializer_data.errors}, status=status.HTTP_400_BAD_REQUEST
            )


class ClientRegisterRequest(APIView):

    def post(self, request):
        onboarding_register_serializer = OnboardingRegisterSerializer(data=request.data)

        if onboarding_register_serializer.is_valid():
            onboarding_register_serializer.save()
            return Response(
                {
                    "data": onboarding_register_serializer.data,
                    "message": "Registration Successful.",
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            onboarding_register_serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class ClientEmailVerifyApiView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        otp = randint(1000, 9999)
        subject = "Email Verification on OneUp Brand Site"
        message = f"Dear customer, your OTP is {otp} for OneUpBrands Client Verification.\nPlease do not share OTP with others.-OneUpBrands"
        from_email = settings.MAIL_HOST_INFO

        try:
            check_email = ClientEmailVerify.objects.get(email=email)
            check_email.otp = otp
            check_email.save()
            send_mail(subject, message, from_email, [email])
            return Response(
                {"message": "Resend OTP on your email."}, status=status.HTTP_200_OK
            )
        except ClientEmailVerify.DoesNotExist:
            ClientEmailVerify.objects.create(email=email, otp=otp)
            send_mail(subject, message, from_email, [email])
            return Response(
                {"message": "Send OTP on your email."}, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClientOtpVerifyApiView(APIView):

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        serializer = ClientEmailVerifySerializer(data={"email": email, "otp": otp})
        if serializer.is_valid():
            enter_otp = serializer.validated_data["otp"]
            enter_email = serializer.validated_data["email"]
            verify_client = ClientEmailVerify.objects.filter(email=enter_email).first()

            if verify_client and verify_client.otp == enter_otp:
                verify_client.verified = True
                verify_client.save()
                return JsonResponse({"Verified": True})
            else:
                return JsonResponse(
                    {"Verified": False}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingStepone(APIView):
    def post(self, request):
        request_user_id = request.data.get("request_user")

        if not request_user_id:
            return JsonResponse(
                {"error": "request_user is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Assuming RequestBussinessRegister is the model for request_user
            request_user = RequestBussinessRegister.objects.get(pk=request_user_id)
        except RequestBussinessRegister.DoesNotExist:
            return JsonResponse(
                {"error": "request_user not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            gst_record = OnboardingGstVerify.objects.get(request_user=request_user)
            request_gst_serializer = OnboardingGstSerializer(
                gst_record, data=request.data
            )
        except OnboardingGstVerify.DoesNotExist:
            request_gst_serializer = OnboardingGstSerializer(data=request.data)

        if request_gst_serializer.is_valid():
            request_gst_serializer.save()
            return Response(
                {"data": request_gst_serializer.data, "message": "Success"},
                status=status.HTTP_200_OK,
            )
        else:
            return JsonResponse(
                {"error": request_gst_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


class OnboardingSteptwo(APIView):
    def post(self, request):
        onboarding_gst_verify_id = request.data.get("onboarding_gst_verify")
        if not onboarding_gst_verify_id:
            return Response(
                {"message": "onboarding_gst_verify is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            onboarding_gst_verify = OnboardingGstVerify.objects.get(
                pk=onboarding_gst_verify_id
            )
        except OnboardingGstVerify.DoesNotExist:
            return Response(
                {"message": "onboarding_gst_verify does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            instance = OnboardingBussinessDetails.objects.get(
                onboarding_gst_verify=onboarding_gst_verify
            )
            serializer = OnboardingBussinessDetailsSerializer(
                instance, data=request.data
            )
        except OnboardingBussinessDetails.DoesNotExist:
            serializer = OnboardingBussinessDetailsSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "message": "Success"},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.parsers import MultiPartParser, FormParser


class OnboardingStepthree(APIView):
    pass
    
    # def post(self, request):
    #     onboarding_bussiness_details_id = request.data.get(
    #         "onboarding_bussiness_details"
    #     )
    #     if not onboarding_bussiness_details_id:
    #         return Response(
    #             {"message": "onboarding_bussiness_details is required"},
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    #     try:
    #         onboarding_bussiness_details = OnboardingBussinessDetails.objects.get(
    #             pk=onboarding_bussiness_details_id
    #         )
    #     except OnboardingBussinessDetails.DoesNotExist:
    #         return Response(
    #             {"message": "onboarding_bussiness_details does not exist"},
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    #     try:
    #         instance = OnboardingAlternativePersonDetails.objects.get(
    #             onboarding_bussiness_details=onboarding_bussiness_details
    #         )
    #         serializer = OnboardingAlternativePersonDetailsSerializer(
    #             instance, data=request.data
    #         )
    #     except OnboardingAlternativePersonDetails.DoesNotExist:
    #         serializer = OnboardingAlternativePersonDetailsSerializer(data=request.data)

    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(
    #             {"data": serializer.data, "message": "Success"},
    #             status=status.HTTP_201_CREATED,
    #         )
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OnboardingStepfour(APIView):
    pass
    # parser_classes = (MultiPartParser, FormParser)

    # def post(self, request):
    #     serializer = OnboardingBankDetailsSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         onboarding_bank_details = OnboardingBankDetails.objects.get(
    #             onboarding_alternative_perDetails=serializer.validated_data[
    #                 "onboarding_alternative_perDetails"
    #             ].id
    #         )
    #         alternative_model_data = OnboardingAlternativePersonDetails.objects.get(
    #             pk=serializer.validated_data["onboarding_alternative_perDetails"].id
    #         )
    #         bussiness_model_data = OnboardingBussinessDetails.objects.get(
    #             pk=alternative_model_data.onboarding_bussiness_details.id
    #         )
    #         gst_model_data = OnboardingGstVerify.objects.get(
    #             pk=bussiness_model_data.onboarding_gst_verify.id
    #         )
    #         register_buss_model_data = RequestBussinessRegister.objects.get(
    #             pk=gst_model_data.request_user.id
    #         )

    #         request_client_data = ClientRequestDetails.objects.create(
    #             request_user=register_buss_model_data,
    #             onboarding_gst_verify=gst_model_data,
    #             onboarding_bussiness_details=bussiness_model_data,
    #             onboarding_alternative_perDetails=alternative_model_data,
    #             onboarding_bank_details=onboarding_bank_details,
    #             status="Requested",
    #             created_at=timezone.now(),
    #         )
    #         return Response(
    #             {"data": serializer.data, "message": "Your Request Send Successfully."},
    #             status=status.HTTP_201_CREATED,
    #         )
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientRequestDetailsList(View):
    template_name = "useraccount/client_request_list.html"

    def get(self, request):
        client_request_data = ClientRequestDetails.objects.all().order_by("-created_at")
        paginator = Paginator(client_request_data, 20)  # Show 10 users per page

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return render(
            request,
            self.template_name,
            {"client_request_data": client_request_data, "page_obj": page_obj},
        )

    def post(self, request):
        email = request.POST.get("email")
        gst_no = request.POST.get("gst_no")
        mobile_no = request.POST.get("mobile_no")
        searched_email = email
        searched_gst_no = gst_no
        searched_mobile_no = mobile_no

        # Filter data based on the input provided
        client_request_data = ClientRequestDetails.objects.all()
        if email:
            client_request_data = client_request_data.filter(
                request_user__email__icontains=email
            )
        elif gst_no:
            client_request_data = client_request_data.filter(
                onboarding_gst_verify__gst_number__icontains=gst_no
            )
        elif mobile_no:
            client_request_data = client_request_data.filter(
                request_user__mobile_number__icontains=mobile_no
            )

        return render(
            request,
            self.template_name,
            {
                "client_request_data": client_request_data,
                "searched_email": searched_email,
                "searched_gst_no": searched_gst_no,
                "searched_mobile_no": searched_mobile_no,
            },
        )


class ClientRequestDetailsUpdate(View):
    template_name = "useraccount/client_request_update.html"

    def get(self, request, pk):
        edit = self.request.session.get("edit", False)
        client_request_data = ClientRequestDetails.objects.get(pk=pk)
        if edit:
            self.request.session["edit"] = False
            return render(
                request,
                self.template_name,
                {"client_request_data": client_request_data, "pk": pk},
            )
        else:
            self.request.session["edit"] = False
            return render(
                request,
                "useraccount/client_request_not_edit.html",
                {"client_request_data": client_request_data, "pk": pk},
            )

    def post(self, request, pk):
        self.request.session["edit"] = True
        return redirect(reverse("ClientRequestUpdate", kwargs={"pk": pk}))


from django.urls import reverse


class ClientRequestDetailsAction(View):
    def post(self, request, pk):
        logger.debug(f"{self.request.POST}")
        status_data = self.request.POST.get("status")

        try:
            client_request_data = ClientRequestDetails.objects.get(pk=pk)
        except ClientRequestDetails.DoesNotExist:
            messages.error(request, "Client request not found.")
            return redirect("ClientRequestList")

        if status_data == "Accepted":
            return self.handle_accepted_request(client_request_data, request)
        elif status_data == "Rejected":
            return self.handle_rejected_request(client_request_data, request)
        elif status_data == "Hold":
            return self.handle_hold_request(client_request_data, request)
        else:
            return HttpResponse("Invalid status provided")

    def handle_accepted_request(self, client_request_data, request):
        try:
            primary_contact_person = client_request_data.request_user.primary_contact_person
            name_parts = primary_contact_person.split(" ", 1)
            first_name, last_name = (
                name_parts if len(name_parts) == 2 else (primary_contact_person, "")
            )

            password = User.objects.make_random_password()
            user = User(
                username=client_request_data.request_user.email,
                email=client_request_data.request_user.email,
                password=make_password(password),
                first_name=first_name,
                last_name=last_name,
            )
            with transaction.atomic():
                try:
                    user.save()
                except IntegrityError as e:
                    logger.debug("Error in saving user: %s", e, exc_info=True)
                    messages.error(request, "User already exists.")
                    return redirect("ClientRequestList")

                # Add User to Group
                user_group, created = Group.objects.get_or_create(name="client")
                user.groups.add(user_group)

                try:
                    client_details = ClientDetails(
                        user=user,
                        designation=client_request_data.request_user.designation,
                        primary_contact_person=client_request_data.request_user.primary_contact_person,
                        mobile_no=client_request_data.request_user.mobile_number,
                        company_name=client_request_data.request_user.bussiness_name,
                        gst_no=client_request_data.onboarding_gst_verify.gst_number,
                        pancard_no=client_request_data.onboarding_gst_verify.pancard_no,
                     
                        date_of_establishment=client_request_data.onboarding_gst_verify.date_of_establishment,

                        first_company_type=client_request_data.onboarding_bussiness_details.first_company_type,
                        industry_type=client_request_data.onboarding_bussiness_details.industry_type,
                        website_link=client_request_data.onboarding_bussiness_details.website_link,



                        upload_pan=client_request_data.onboarding_bank_details.upload_pan,
                        upload_gst=client_request_data.onboarding_bank_details.upload_gst,
                        certificate_of_corporation=client_request_data.onboarding_bank_details.certificate_of_corporation,
                        msme=client_request_data.onboarding_bank_details.msme,
                        authorization_letter=client_request_data.onboarding_bank_details.authorization_letter,
                        adhaar=client_request_data.onboarding_bank_details.aadhar,

                        communication_postal_code=client_request_data.onboarding_comm_ad.communication_postal_code,
                        communication_country=client_request_data.onboarding_comm_ad.communication_country,
                        communication_state=client_request_data.onboarding_comm_ad.communication_state,
                        communication_city=client_request_data.onboarding_comm_ad.communication_city,
                        communication_address=client_request_data.onboarding_comm_ad.communication_address,

                        reg_postal_code=client_request_data.onboarding_reg_ad.reg_postal_code,
                        reg_country=client_request_data.onboarding_reg_ad.reg_country,
                        reg_state=client_request_data.onboarding_reg_ad.reg_state,
                        reg_city=client_request_data.onboarding_reg_ad.reg_city,
                        reg_address=client_request_data.onboarding_reg_ad.reg_address,

                        warehouse_postal_code = client_request_data.onboarding_Warehouse_ad.warehouse_postal_code,
                        

                        warehouse_country = client_request_data.onboarding_Warehouse_ad.warehouse_country,
                        warehouse_state = client_request_data.onboarding_Warehouse_ad.warehouse_state,
                        warehouse_city = client_request_data.onboarding_Warehouse_ad.warehouse_city,
                        warehouse_address = client_request_data.onboarding_Warehouse_ad.warehouse_address,





                        outlet_postal_code =client_request_data.onboarding_OutletAddress_ad.outlet_postal_code,
                        outlet_country = client_request_data.onboarding_OutletAddress_ad.outlet_country,
                        outlet_state = client_request_data.onboarding_OutletAddress_ad.outlet_state,
                        outlet_city = client_request_data.onboarding_OutletAddress_ad.outlet_city,
                        outlet_address = client_request_data.onboarding_OutletAddress_ad.outlet_address,

                    )
                    client_details.save()
                except Exception as e:
                    logger.error("Error occurred in saving client details: %s", e, exc_info=True)
                    if user.id:
                        user.delete()
                    messages.error(request, f"Error : {e}")
                    return redirect("ClientRequestList")

                unique_string_obj = UniqueStrings.objects.filter(user=client_details.user).first()
                data = {
                    "name": f"{first_name} {last_name}",
                    "customer_id": unique_string_obj.unique_string,
                    "customer_type": "Client",
                }
                send_client_data_to_user(data)

                cou = Country.objects.filter(name="Republic of India").first()
                user_add = UserAddress(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    email=client_details.user.email,


                    line1=client_details.communication_address,
                    line4=client_details.communication_city,
                    state=client_details.communication_state,
                    postcode=client_details.communication_postal_code,
                


           





                    country=cou,
                    phone_number=client_details.mobile_no,
                )

                try:
                    user_add.save()
                except IntegrityError as e:
                    logger.debug("Error in saving user address: %s", e, exc_info=True)
                    if user_add.id:
                        user_add.delete()
                    messages.error(request, "Error occurred in saving user address.")
                    return redirect("ClientRequestList")

                # Attempt to send the email
                subject = "Your Business Account Registration is Complete"
                message = (
                    f"This is your Email and Password:\n\nEmail: {client_details.user.email}\n"
                    f"Password: {password}\n Unique User ID: {unique_string_obj.unique_string}"
                )
                message = (
                    f"Dear {first_name} {last_name},\n\n"
                    f"We are pleased to inform you that your business account registration for {client_details.company_name} with One Up Brands has been successfully processed.\n\n"
                    f"Below are your account details:\n\n"
                    f"User ID: {unique_string_obj.unique_string}\n"
                    f"Temporary Password: {password}\n\n"
                    f"For security reasons, we recommend that you log in to your account and change your password immediately.\n\n"
                    f"Login Instructions:\n\n"
                    f"1. Visit https://oneupbrands.com/clientlogin.\n"
                    f"2. Enter your User ID and the temporary password provided above.\n"
                    f"3. Change Your Password in the My Profile section.\n\n"
                    f"If you have any questions or need assistance with your account, our team is here to help.\n\n"
                    f"Thank you for choosing One Up Brands. \n\n"
                    f"Best regards,\n"
                    f"Support Team\n"
                    f"One Up Brands"
                    )

                from_email = settings.MAIL_HOST_INFO
                to_email = [client_details.user.email]
   

    

                try:
                    send_mail(subject, message, from_email, to_email)
                    # Send notification mail
                    self.send_notification_mail(client_details)
                except Exception as e:
                    logger.error("Error occurred while sending the email: %s", e, exc_info=True)
                    # Rollback changes if email sending fails
                    if client_details.id:
                        client_details.delete()
                    if user.id:
                        user.delete()
                    if user_add.id:
                        user_add.delete()

                    messages.error(request, f"An error occurred while sending the email: {e}")
                    return redirect("ClientRequestUpdate", pk=client_request_data.pk)

                # Mark client request as accepted and delete it
                client_request_data.status = "Accepted"
                client_request_data.delete()

                messages.success(
                    request,
                    "Client is successfully accepted and an email has been sent to the client.",
                )

        except Exception as e:
            logger.error("An error occurred during the client acceptance process: %s", e, exc_info=True)

            messages.error(request, f"An error occurred: {e}")
            return redirect("ClientRequestUpdate", pk=client_request_data.pk)

        return redirect("ClientRequestList")

    def handle_rejected_request(self, client_request_data, request):
        rejection_reason = self.request.POST.get("rejection_reason", "")

        primary_contact_person = client_request_data.request_user.primary_contact_person
        name_parts = primary_contact_person.split(" ", 1)
        first_name, last_name = (
            name_parts if len(name_parts) == 2 else (primary_contact_person, "")
        )

        try:
            client_request_data.status = "Rejected"
            client_request_data.save()

            subject = "Business Account Registration Update"
            # message = f"Your request has been rejected. Reason: {rejection_reason}"

            message = (
            f"Subject: Business Account Registration Update\n\n"
            f"Dear {first_name} {last_name},\n\n"
            f"Thank you for your interest in registering a business account for {client_request_data.request_user.bussiness_name} with One Up Brands. After carefully reviewing your application, please note that your registration request cannot be processed at this time due to the following reason(s):\n\n"
            f"{rejection_reason}\n\n"
            f"Please note that you are welcome to reapply in the future once the above issue(s) have been resolved.\n\n"
            f"Best regards,\n"
            f"Support Team\n"
            f"One Up Brands"
            )

            email_from = settings.MAIL_HOST_INFO
            recipient_list = [client_request_data.request_user.email]

            send_mail(subject, message, email_from, recipient_list)
            messages.success(request, "Client request rejected successfully.")

            redirect_url = reverse(
                "ClientRequestUpdate", kwargs={"pk": client_request_data.pk}
            )
            return redirect(redirect_url)
        except Exception as e:
            # Log any errors during the process
            client_request_data.status = "Requested"
            client_request_data.save()
            messages.error(request, f"An error occurred while sending a email.: {e}")
            return redirect("ClientRequestUpdate", pk=client_request_data.pk)


    def handle_hold_request(self, client_request_data, request):
        hold_reason = self.request.POST.get("hold_reason", "")
        primary_contact_person = client_request_data.request_user.primary_contact_person
        name_parts = primary_contact_person.split(" ", 1)
        first_name, last_name = (
            name_parts if len(name_parts) == 2 else (primary_contact_person, "")
        )
        # Mapping of form field names to model field names
        document_fields = {
            "aadhar_card": "aadhar",
            "authorization_letter": "authorization_letter",
            "msme": "msme",
            "certificate_of_corporation": "certificate_of_corporation",
            "upload_gst": "upload_gst",
            "upload_pan": "upload_pan",
        }

        # Fetch corresponding image paths from the database
        image_paths = []
        marked_documents = []

        for form_field, model_field in document_fields.items():
            if request.POST.get(form_field):  # Check if this document was selected
                document = getattr(client_request_data.onboarding_bank_details, model_field, None)
                if document:  # Ensure the document exists
                    document_path = document.path  # Get the full path of the document

                    # Debug: Log the document path
                    logger.debug(f"Checking file path for {model_field}: {document_path}")

                    from django.core.files.storage import default_storage
                    if default_storage.exists(document_path):  # Check if the file exists on the server
                        image_paths.append(document_path)
                        marked_documents.append(document_fields[form_field])  # Track the document name

                    else:
                        # Log and notify about the missing file
                        logger.error(f"File not found: {document_path}")
                        messages.error(request, f"File not found: {document_path}")
                        return redirect("ClientRequestUpdate", pk=client_request_data.pk)

        try:
            # Update the status of the client request
            client_request_data.status = "Hold"
            client_request_data.save()

            # Prepare the email
            subject = "Your request has been put on hold"
            # message = f"Your request has been put on hold. Reason: {hold_reason}"
            message = (
            f"Dear {first_name} {last_name},\n\n"
            f"While reviewing your account registration form and details, our administrative team has identified the following errors:\n\n"
            f"{hold_reason}\n\n"
            f"Please share the below documents:\n"
            f"{', '.join(marked_documents)}\n\n"
            f"To proceed with the registration, please reply to this email with clarification regarding the reasons mentioned above and/or attach any supporting or requested documents. Once the issue is resolved, we will promptly continue with the registration process.\n\n"
            f"Best regards,\n"
            f"Support Team\n"
            f"One Up Brands"
        )
            email_from = settings.MAIL_HOST_INFO
            recipient_list = [client_request_data.request_user.email]

            from django.core.mail import EmailMessage
            email = EmailMessage(subject, message, email_from, recipient_list)

            # Attach selected documents to the email
            for image_path in image_paths:
                email.attach_file(image_path)

            # Send the email
            email.send()
            messages.success(request, "Client request put on hold and email sent with attachments.")

        except Exception as e:
            # Log any errors during the process
            client_request_data.status = "Requested"
            client_request_data.save()
            messages.error(request, f"An error occurred while sending a email : {e}")
            return redirect("ClientRequestUpdate", pk=client_request_data.pk)

        # Redirect back to the client request update page
        return redirect("ClientRequestUpdate", pk=client_request_data.pk)

    def send_notification_mail(self, client_details):
        subject = "New Client Registered on Site"
        message = (
            f"Here is a new client registered on OneUp Brand:\n\n"
            f"Company Name: {client_details.company_name}\n"
            f"Email: {client_details.user.email}\n"
            f"Mobile Number: {client_details.mobile_no}\n"
        )
        from_email = settings.EMAIL_HOST_USER
        to_email = [settings.EMAIL_HOST_USER]

        try:
            send_mail(subject, message, from_email, to_email)
        except Exception as e:
            logger.error(f"Failed to send notification email: {e}")


class ClientRequestDetailsSave(View):
    def post(self, request, pk):
        logger.debug(f"{self.request.POST=}")
        client_request_data = ClientRequestDetails.objects.get(pk=pk)
        request_user = client_request_data.request_user
        request_user.primary_contact_person = self.request.POST.get(
            "primary_contact_person"
        )

        request_user.designation = self.request.POST.get("designation")
        request_user.email = self.request.POST.get("email")
        request_user.mobile_number = self.request.POST.get("mobile_number")
        request_user.bussiness_name = self.request.POST.get("bussiness_name")
       
        request_user.save()
        onboarding_gst_verify = client_request_data.onboarding_gst_verify

        if len(self.request.POST.get("gst_number").lstrip()) == 0:
            onboarding_gst_verify.gst_number = None
            print(self.request.POST.get("gst_number"), "space")
        else:
            onboarding_gst_verify.gst_number = self.request.POST.get("gst_number")
            print(self.request.POST.get("gst_number"), "no space")

  
        onboarding_gst_verify.date_of_establishment = self.request.POST.get(
            "date_of_establishment"
        )

        onboarding_gst_verify.pancard_no = self.request.POST.get("pancard_no")
        onboarding_gst_verify.save()

        onboarding_bussiness_details = client_request_data.onboarding_bussiness_details

        onboarding_bussiness_details.first_company_type = self.request.POST.get(
            "first_company_type"
        )
  
        onboarding_bussiness_details.industry_type = self.request.POST.get(
            "industry_type"
        )
        onboarding_bussiness_details.website_link = self.request.POST.get(
            "website_link"
        )
        onboarding_bussiness_details.save()
        # change to whwre houe


        onboarding_onboarding_Warehouse_ad = client_request_data.onboarding_Warehouse_ad

        onboarding_onboarding_Warehouse_ad. warehouse_postal_code = self.request.POST.get(
            "warehouse_postal_code"
        ) 
        onboarding_onboarding_Warehouse_ad.warehouse_address = self.request.POST.get(
            "warehouse_address"
        )
        onboarding_onboarding_Warehouse_ad.warehouse_city = self.request.POST.get(
            "warehouse_city"
        )
        onboarding_onboarding_Warehouse_ad.warehouse_state = self.request.POST.get(
            "warehouse_state"
        )
        onboarding_onboarding_Warehouse_ad.warehouse_country = self.request.POST.get(
            "warehouse_country"
        )
        onboarding_onboarding_Warehouse_ad.save()


        # wherehouse end


         # change to outlet 


        onboarding_onboarding_OutletAddress_ad = client_request_data.onboarding_OutletAddress_ad

        onboarding_onboarding_OutletAddress_ad. outlet_postal_code = self.request.POST.get(
            "outlet_postal_code"
        ) 
        onboarding_onboarding_OutletAddress_ad.outlet_address = self.request.POST.get(
            "outlet_address"
        )
        onboarding_onboarding_OutletAddress_ad.outlet_city = self.request.POST.get(
            "outlet_city"
        )
        onboarding_onboarding_OutletAddress_ad.outlet_state = self.request.POST.get(
            "outlet_state"
        )
        onboarding_onboarding_OutletAddress_ad.outlet_country = self.request.POST.get(
            "outlet_country"
        )
        onboarding_onboarding_OutletAddress_ad.save()


        # outlet end

     
        # test


        onboarding_OnboardingRegisteredAddress = client_request_data.onboarding_reg_ad

        onboarding_OnboardingRegisteredAddress.reg_postal_code = self.request.POST.get(
            "reg_postal_code"
        ) 
        onboarding_OnboardingRegisteredAddress.reg_address = self.request.POST.get(
            "reg_address"
        )
        onboarding_OnboardingRegisteredAddress.reg_city = self.request.POST.get(
            "reg_city"
        )
        onboarding_OnboardingRegisteredAddress.reg_state = self.request.POST.get(
            "reg_state"
        )
        onboarding_OnboardingRegisteredAddress.reg_country = self.request.POST.get(
            "reg_country"
        )
        onboarding_OnboardingRegisteredAddress.save()
        # test



           # test two
        onboarding_OnboardingCommunication = client_request_data.onboarding_comm_ad

        onboarding_OnboardingCommunication.communication_postal_code = self.request.POST.get(
            "communication_postal_code"
        ) 
        onboarding_OnboardingCommunication.communication_address = self.request.POST.get(
            "communication_address"
        )
        onboarding_OnboardingCommunication.communication_city = self.request.POST.get(
            "communication_city"
        )
        onboarding_OnboardingCommunication.communication_state = self.request.POST.get(
            "reg_state"
        )
        onboarding_OnboardingCommunication.communication_country = self.request.POST.get(
            "communication_state"
        )
        onboarding_OnboardingCommunication.save()
        # test two

        onboarding_bank_details = client_request_data.onboarding_bank_details
        

        if request.FILES.get("upload_pan"):
            onboarding_bank_details.upload_pan = request.FILES.get("upload_pan")

        if request.FILES.get("upload_gst"):
            onboarding_bank_details.upload_gst = request.FILES.get("upload_gst")

        if request.FILES.get("certificate_of_corporation"):
            onboarding_bank_details.certificate_of_corporation = request.FILES.get(
                "certificate_of_corporation"
            )

        if request.FILES.get("msme"):
            onboarding_bank_details.msme = request.FILES.get("msme")

        if request.FILES.get("authorization_letter"):
            onboarding_bank_details.authorization_letter = request.FILES.get(
                "authorization_letter"
            )

        if request.FILES.get("aadhar"):
            onboarding_bank_details.aadhar = request.FILES.get(
                "aadhar"
            )

        onboarding_bank_details.save()

        return redirect(reverse("ClientRequestUpdate", kwargs={"pk": pk}))


def download_client_request_log(request):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Client Request List"

    headers = [
        "S.No",
        "Name",
        "Email",
        "GST No.",
        "Mobile No.",
        "Status",
        "Date Requested",
    ]
    worksheet.append(headers)

    logs = ClientRequestDetails.objects.all().order_by("-created_at")

    for index, log in enumerate(logs, start=1):
        worksheet.append(
            [
                index,
                log.request_user.primary_contact_person,
                log.request_user.email,
                log.onboarding_gst_verify.gst_number,
                log.request_user.mobile_number,
                log.status,
                log.created_at.strftime("%d/%m/%Y %H:%M"),
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        "attachment; filename=client_request_list_log.xlsx"
    )

    workbook.save(response)

    return response


# Get Help View
class GetHelpOnHomePageAPIView(APIView):
    def post(self, request):
        # Instantiate the serializer with the incoming data
        serializer = GetHelpOnHomePageSerializer(data=request.data)

        # Validate and deserialize the data
        if serializer.is_valid():
            # Save the validated data to the database
            serializer.save()

            # Return a success response
            return Response(
                {
                    "status": "success",
                    "message": "Your request has been submitted successfully.",
                },
                status=status.HTTP_201_CREATED,
            )

        # Return an error response if validation fails
        return Response(
            {
                "status": "error",
                "message": "Validation error",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class GetHelpOnHomePageView(View):
    template_name = "useraccount/get_help_list.html"

    def get(self, request):
        get_help_data = GetHelpOnHomePage.objects.all().order_by("-created_at")

        return render(request, self.template_name, {"get_help_data": get_help_data})


class GetHelpOnHomePageDeleteView(View):
    def get(self, request, pk):
        get_delete_data = GetHelpOnHomePage.objects.get(pk=pk)

        if get_delete_data:
            get_delete_data.delete()
            messages.success(request, f"{get_delete_data.email} is deleted.")
        else:
            messages.error(request, f"Something Went Wrong!")

        return redirect("get-help-list")


class GetHelpOnHomePageDetailsView(View):
    template_name = "useraccount/get_help_details.html"

    def get(self, request, pk):
        get_details_data = GetHelpOnHomePage.objects.get(pk=pk)

        if not get_details_data:
            messages.success(request, "Get Help Not Found.")
            return redirect("get-help-list")

        return render(
            request, self.template_name, {"get_details_data": get_details_data}
        )


class CleintREgisterTotalAPi(APIView):

    def post(self, request):
        import json

        data = json.loads(request.data.get("json_data"))
        
        logger.debug(request.data)


       

        bank = FullDataSerializer(data=request.data)
        logger.debug(bank.is_valid())
        logger.debug(bank.errors)

        onboarding_register_serializer = OnboardingRegisterSerializer(
            data=data.get("business")
        )
        logger.debug(f"after first line {data.get('business')}")

        if onboarding_register_serializer.is_valid():
            onboarding_register_serializer.save()
        else:
            logger.debug(onboarding_register_serializer.errors)
            return Response(
                {"error": "data not valid"}, status=status.HTTP_400_BAD_REQUEST
            )
        request_user_id = onboarding_register_serializer.data["id"]
        logger.debug(request_user_id)

        if not request_user_id:
            return JsonResponse(
                {"error": "request_user is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            request_user = RequestBussinessRegister.objects.get(pk=request_user_id)
        except RequestBussinessRegister.DoesNotExist:
            return JsonResponse(
                {"error": "request_user not found"}, status=status.HTTP_404_NOT_FOUND
            )
        logger.debug("reached gst")
        data["gst"]["request_user"] = request_user_id
        try:
            gst_record = OnboardingGstVerify.objects.get(request_user=request_user)
            request_gst_serializer = OnboardingGstSerializer(
                gst_record, data=data.get("gst")
            )
        except OnboardingGstVerify.DoesNotExist:
            request_gst_serializer = OnboardingGstSerializer(data=data.get("gst"))

        if request_gst_serializer.is_valid():
            request_gst_serializer.save()

        else:
            return JsonResponse(
                {"error": request_gst_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        onboarding_gst_verify_id = request_gst_serializer.data["id"]
        if not onboarding_gst_verify_id:
            return Response(
                {"message": "onboarding_gst_verify is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.debug("reached gst verify2")
        try:
            onboarding_gst_verify = OnboardingGstVerify.objects.get(
                pk=onboarding_gst_verify_id
            )
        except OnboardingGstVerify.DoesNotExist:
            return Response(
                {"message": "onboarding_gst_verify does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.debug("reached businessdeta verify")
        data["bussiness_details"]["onboarding_gst_verify"] = onboarding_gst_verify_id
        try:
            instance = OnboardingBussinessDetails.objects.get(
                onboarding_gst_verify=onboarding_gst_verify
            )
            serializer = OnboardingBussinessDetailsSerializer(
                instance, data=data.get("bussiness_details")
            )
        except OnboardingBussinessDetails.DoesNotExist:
            serializer = OnboardingBussinessDetailsSerializer(
                data=data.get("bussiness_details")
            )

        logger.debug("complet reached businessdeta verify")
        if serializer.is_valid():
            serializer.save()

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        onboarding_bussiness_details_id = serializer.data["id"]
        if not onboarding_bussiness_details_id:
            return Response(
                {"message": "onboarding_bussiness_details is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            onboarding_bussiness_details = OnboardingBussinessDetails.objects.get(
                pk=onboarding_bussiness_details_id
            )
        except OnboardingBussinessDetails.DoesNotExist:
            return Response(
                {"message": "onboarding_bussiness_details does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        logger.debug("no were on earth reached businessdeta verify")
        # data["alt_person"]["onboarding_bussiness_details"] = onboarding_bussiness_details_id 
        # no need above line
        # try:
        #     instance = OnboardingAlternativePersonDetails.objects.get(
        #         onboarding_bussiness_details=onboarding_bussiness_details
        #     )
        #     serializer = OnboardingAlternativePersonDetailsSerializer(
        #         instance, data=data.get("alt_person")
        #     )
        # except OnboardingAlternativePersonDetails.DoesNotExist:
        #     serializer = OnboardingAlternativePersonDetailsSerializer(
        #         data=data.get("alt_person")
        #     )

        # if serializer.is_valid():
        #     serializer.save()

        # else:
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # id_alt_details = serializer.data["id"]

        # request.data["onboarding_alternative_perDetails"] = id_alt_details
        request.data["onboarding_bussiness_details"] = onboarding_bussiness_details_id

        bankSerializer = OnboardingBankDetailsSerializer(data=request.data)
        if bankSerializer.is_valid():
            bankSerializer.save()
        else:
            return Response(bankSerializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data["comm"]["onboarding_bank_details"] = bankSerializer.data["id"]
        comm_serializer = OnboardingCommunictionSerializer(data=data.get("comm"))
        if comm_serializer.is_valid():
            comm_serializer.save()
        else:
            return Response(comm_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        logger.debug("after comm")

        data["reg"]["onboarding_comm_details"] = comm_serializer.data["id"]
        reg_add_serializer = OnboardingregisterAddressSerializer(data=data.get("reg"))

        if reg_add_serializer.is_valid():
            reg_add_serializer.save()
        else:
            return Response(reg_add_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        logger.debug("reg_add_serializer comm")

        data["warehouse"]["onboarding_reg_details"] = reg_add_serializer.data["id"]
        warehouse_add_serializer = OnboardingWarehouseAddressSerializer(data=data.get("warehouse"))

        if warehouse_add_serializer.is_valid():
            warehouse_add_serializer.save()
        else:
            return Response(warehouse_add_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        logger.debug(" AFTER : warehouse_add_serializer ")

        data["outlet"]["onboarding_warehouse_details"] = warehouse_add_serializer.data["id"]
        outlet_add_serializer = OnboardingOutletAddresssSerializer(data=data.get("outlet"))



        if outlet_add_serializer.is_valid():
            outlet_add_serializer.save()
        else:
            return Response(
                outlet_add_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        logger.debug("after reg")

        if reg_add_serializer.is_valid():
            onboarding_bank_details = OnboardingBankDetails.objects.get(
                onboarding_bussiness_details=onboarding_bussiness_details_id
            )
            # alternative_model_data = OnboardingAlternativePersonDetails.objects.get(
            #     pk=bankSerializer.validated_data["onboarding_alternative_perDetails"].id
            # )
            # 
            bussiness_model_data = OnboardingBussinessDetails.objects.get(
                pk=onboarding_bussiness_details_id
            )
            gst_model_data = OnboardingGstVerify.objects.get(
                pk=bussiness_model_data.onboarding_gst_verify.id
            )
            register_buss_model_data = RequestBussinessRegister.objects.get(
                pk=gst_model_data.request_user.id
            )
            comm_model = OnboardingCommunication.objects.get(
                onboarding_bank_details=onboarding_bank_details
            )
            reg_model = OnboardingRegisteredAddress.objects.get(
                onboarding_comm_details=comm_model
            )
            warehouse_model = WarehouseAddress.objects.get(
                onboarding_reg_details=reg_model
            )
            Outlet_model = OutletAddress.objects.get(
                onboarding_warehouse_details=warehouse_model
            )

            request_client_data = ClientRequestDetails.objects.create(
                request_user=register_buss_model_data,
                onboarding_gst_verify=gst_model_data,
                onboarding_bussiness_details=bussiness_model_data,
                # onboarding_alternative_perDetails=alternative_model_data,
                onboarding_bank_details=onboarding_bank_details,
                status="Requested",
                created_at=timezone.now(),
                onboarding_comm_ad=comm_model,
                onboarding_reg_ad=reg_model,
                onboarding_Warehouse_ad=warehouse_model,
                onboarding_OutletAddress_ad=Outlet_model

            )
            return Response(
                {"data": serializer.data, "message": "Your Request Send Successfully."},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckGstAlreadyExists(APIView):
    def post(self, request):
        gst = request.data.get("gst")

        gst_data = ClientDetails.objects.filter(gst_no=gst)

        if not gst_data:
            return Response({"data": "Gst Does Not Exists."}, status=status.HTTP_200_OK)
        else:
            return Response({"data": "Gst Already Exists."}, status=status.HTTP_200_OK)


class CheckEmailAlreadyExists(APIView):
    def post(self, request):
        email = request.data.get("email")

        user_exists = User.objects.filter(username=email).exists()
        email_exists = User.objects.filter(email=email).exists()
        email_exists_in_business = RequestBussinessRegister.objects.filter(email=email).exists()


        if user_exists or email_exists or email_exists_in_business:
            return Response(
                {"data": "Email Already Exists."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"data": "Email Does Not Exists."}, status=status.HTTP_200_OK
            )

        # email_data = User.objects.filter(email=email)
        

        # if email_data:
        #     return Response(
        #         {"data": "Email Already Exists."}, status=status.HTTP_200_OK
        #     )
        # else:
        #     return Response(
        #         {"data": "Email Does Not Exists."}, status=status.HTTP_200_OK
        #     )



voucher_set = get_model("voucher","Voucher")

class VoucherLogin(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        code = request.data.get("code")
        try:
            count = VocherLoginConnect.objects.get(
                                 voucher__code=code
                            ).count
            count = count + 1
        except:
            logger.error("error in voucher login connect",exc_info=True)
            count = 1
        try:
            voucher_obj = voucher_set.objects.get(code=code)
            voucher_amount = voucher_obj.voucher_set.voucherset.voucher_amount
            end_date = voucher_obj.voucher_set.end_datetime
        except:
            return Response({"message":"voucher doesn't exist"},status=status.HTTP_404_NOT_FOUND)
            


        
        serializer = EmailSentSerializer(data=data)
        if serializer.is_valid():
            mobile_number = serializer.validated_data["mobile_number"]
            try:
                mob_obj = UserProfile.objects.get(mobile_number=mobile_number)
            except Exception as e:
                mob_obj = UserProfile.objects.create(mobile_number=mobile_number)

            try:
                mob_obj_2 = ClientDetails.objects.filter(mobile_no=f"+91{mob_obj.mobile_number}").exists()
                mob_obj_3 = ClientDetails.objects.filter(mobile_no=mob_obj.mobile_number).exists()


            except Exception as e:
                mob_obj_2 = None
                mob_obj_3 = None
            if not mob_obj_2  and not mob_obj_3:
                if mob_obj:
                    otp = randint(1000, 9999)
                    mob_obj.otp = otp
                    mob_obj.save()
                    SmsOtpIntegration.send_otp_sms(mobile_number, otp, "customer")
                    return Response({"message": "Otp sent on your mobile number","count":count,"end_date":end_date,"voucher_amount":voucher_amount})
                else:
                    otp = randint(1000, 9999)

                    UserProfile.objects.create(mobile_number=mobile_number, otp=otp)

                    SmsOtpIntegration.send_otp_sms(mobile_number, otp, "customer")

                    return Response({"message": "Otp sent on your mobile number","count":count,"end_date":end_date,"voucher_amount":voucher_amount})
            else:

                return Response(
                    {"message": "Your Mobile Number is already exists in client side."}
                )

        else:
            return Response({"message": "serializer is not valid"})


class ResetPassword(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        data = request.data
        old_pass = data.get("old_password")
        new_pass = data.get("new_password")
        
        user = request.user
        logger.info(user)
        password_is_correct = user.check_password(old_pass)
        logger.info(password_is_correct)
        if password_is_correct:
            user.set_password(new_pass)
            user.save()
            return Response({"message":"password changed"},status=status.HTTP_200_OK)
        else:
            return Response({"message":"incorrect password"},status=status.HTTP_400_BAD_REQUEST)
        

class SendMail(APIView):
    def post(self,request):
        send_mail(subject="none",message="none",from_email="noreply@oneupbrands.com",recipient_list=['pranavpranab@gmail.com'])
        return Response({})