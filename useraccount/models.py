from typing import Iterable
from django.db import models
from django.contrib.auth.models import User
from oscar.apps.voucher.models import Voucher
from wallet.models import Wallet
from credit.models import Credit
import random

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from datetime import datetime
from django.db.models import Max
import logging

logger = logging.getLogger(__name__)


class UserAuthTokens(models.Model):
    user_info = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField(default=0)
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_auth_tokens"


GENDER_CHOICES = [
    ("Male", "Male"),
    ("Female", "Female"),
]


class ClientDetails(models.Model):
    # store sign up page data
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name="client")
    primary_contact_person = models.CharField(max_length=150, blank=True, null=True)
    designation = models.CharField(max_length=150, blank=True, null=True)
    mobile_no = models.CharField(max_length=15)
    company_name = models.CharField(max_length=100)

    # store gst verify data
    gst_no = models.CharField(max_length=50, blank=True, null=True)
    pancard_no = models.CharField(max_length=10, blank=True, null=True)
    # address_line1 = models.CharField(max_length=100)
    # address_line2 = models.CharField(max_length=100, blank=True, null=True)
    # city = models.CharField(max_length=50)
    # state = models.CharField(max_length=50)
    # country = models.CharField(max_length=50)
    # pin_code = models.CharField(max_length=10)
    date_of_establishment = models.DateField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default=" ", blank=True, null=True
    )
    current_date = models.DateTimeField(auto_now_add=True)

    # store bussiness data
    first_company_type = models.CharField(max_length=100, blank=True, null=True)
    # second_company_type = models.CharField(max_length=100, blank=True, null=True)
    industry_type = models.CharField(max_length=100, blank=True, null=True)
    website_link = models.CharField(max_length=255, blank=True, null=True)

    # store alternative data
    # alter_first_address = models.CharField(max_length=255, blank=True, null=True)
    # alter_second_address = models.CharField(max_length=255, blank=True, null=True)
    # alter_postal_code = models.CharField(max_length=10)
    # alter_city = models.CharField(max_length=50)
    # alter_state = models.CharField(max_length=50)
    # alter_country = models.CharField(max_length=50)

    # alternative_mobile = models.CharField(max_length=255, blank=True, null=True)
    # alternative_email = models.CharField(max_length=255, blank=True, null=True)
    # alternative_designation = models.CharField(max_length=255, blank=True, null=True)
    # alternative_person_name = models.CharField(max_length=255, blank=True, null=True)

    # store bank data

    upload_pan = models.ImageField(upload_to="Onboarding/", blank=True, null=True)
    upload_gst = models.ImageField(upload_to="Onboarding/", blank=True, null=True)
    certificate_of_corporation = models.ImageField(
        upload_to="Onboarding/", blank=True, null=True
    )
    msme = models.ImageField(upload_to="Onboarding/", blank=True, null=True)
    authorization_letter = models.ImageField(
        upload_to="Onboarding/", blank=True, null=True
    )
    adhaar = models.ImageField(upload_to="Onboarding/", blank=True, null=True)

    # Onboarding Communication
    communication_postal_code = models.CharField(max_length=10, null=True, blank=True)
    communication_country = models.CharField(max_length=256, null=True, blank=True)
    communication_state = models.CharField(max_length=256, blank=True, null=True)
    communication_city = models.CharField(max_length=256, blank=True, null=True)
    communication_address = models.CharField(max_length=256, blank=True, null=True)
    #--------------------

    # Onboarding Register
    reg_postal_code = models.CharField(max_length=10, null=True, blank=True)
    reg_country = models.CharField(max_length=256, null=True, blank=True)
    reg_state = models.CharField(max_length=256, blank=True, null=True)
    reg_city = models.CharField(max_length=256, blank=True, null=True)
    reg_address = models.CharField(max_length=256, blank=True, null=True)

    # Onboarding Warehouse
    warehouse_postal_code = models.CharField(max_length=10, null=True, blank=True)
    warehouse_country = models.CharField(max_length=256, null=True, blank=True)
    warehouse_state = models.CharField(max_length=256, blank=True, null=True)
    warehouse_city = models.CharField(max_length=256, blank=True, null=True)
    warehouse_address = models.CharField(max_length=256, blank=True, null=True)

    # Onboarding Outlet
    outlet_postal_code = models.CharField(max_length=10, null=True, blank=True)
    outlet_country = models.CharField(max_length=256, null=True, blank=True)
    outlet_state = models.CharField(max_length=256, blank=True, null=True)
    outlet_city = models.CharField(max_length=256, blank=True, null=True)
    outlet_address = models.CharField(max_length=256, blank=True, null=True)

    # --------------------

    # wherehouse Register
    warehouse_postal_code = models.CharField(max_length=10, null=True, blank=True)
    warehouse_country = models.CharField(max_length=256, null=True, blank=True)
    warehouse_state = models.CharField(max_length=256, blank=True, null=True)
    warehouse_city = models.CharField(max_length=256, blank=True, null=True)
    warehouse_address = models.CharField(max_length=256, blank=True, null=True)

    # --------------------


    # outlet Register
    outlet_postal_code = models.CharField(max_length=10, null=True, blank=True)
    outlet_country = models.CharField(max_length=256, null=True, blank=True)
    outlet_state = models.CharField(max_length=256, blank=True, null=True)
    outlet_city = models.CharField(max_length=256, blank=True, null=True)
    outlet_address = models.CharField(max_length=256, blank=True, null=True)

    # --------------------

    def save(
        self,
    ):
        try:
            wallet = self.user.wallet
        except:
            Wallet.objects.create(user=self.user)
        try:
            credits = self.user.credit
        except:
            Credit.objects.create(user=self.user)

        return super().save()

    def __str__(self):
        return self.user.username


@receiver(post_delete, sender=ClientDetails)
def delete_user_when_client_deleted(sender, instance, **kwargs):
    if instance.user:
        instance.user.delete()


class VoucherUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_no = models.CharField(max_length=15)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES,  blank=True, null=True
    )

    def __str__(self) -> str:
        return self.user.first_name


class UserProfile(models.Model):
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    otp = models.IntegerField(default=0)
    otp_verify = models.BooleanField(default=False)
    added_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField()

    def __str__(self):
        return f"{self.otp}"


# Contact_Us_API
class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.first_name} {self.last_name} - {self.email} - {self.phone_number}"
        )

    class Meta:
        ordering = ["-created_at"]


class VocherLoginConnect(models.Model):
    count = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)


class UploadProductJSon(models.Model):
    upload_json = models.JSONField()
    created_date = models.DateTimeField(auto_now_add=True)


class IntermediateProductTableChild(models.Model):
    json_relation = models.ForeignKey(
        UploadProductJSon, on_delete=models.CASCADE, blank=True, null=True
    )
    upc = models.CharField(max_length=254, blank=True, null=True)
    hsn_code = models.CharField(max_length=254, blank=True, null=True)

    title = models.CharField(max_length=254, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    Specification = models.TextField(max_length=254, blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    product_type = models.CharField(max_length=254, blank=True, null=True)
    is_public = models.CharField(max_length=254, blank=True, null=True)
    is_discountable = models.CharField(max_length=254, blank=True, null=True)
    best_seller = models.CharField(max_length=100, blank=True, null=True)
    standard_rate = models.CharField(max_length=254, blank=True, null=True)
    num_in_stock = models.CharField(max_length=100, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    first_category = models.CharField(max_length=254, blank=True, null=True)
    attributes = models.TextField(blank=True, null=True)
    Parent_UPC = models.CharField(max_length=254, blank=True, null=True)
    structure = models.CharField(max_length=100, blank=True, null=True)

    recommended_products = models.TextField(blank=True, null=True)

    length = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    supplier = models.CharField(max_length=254, blank=True, null=True)
    low_stock_threshold = models.CharField(max_length=254, blank=True, null=True)
    mrp = models.IntegerField(blank=True, null=True)
    discount = models.IntegerField(blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    gst_rate = models.CharField(max_length=254, blank=True, null=True)
    product_status = models.CharField(max_length=100, default="Pending Creation")

    def __str__(self):
        return f"{self.upc}"


class ClientEmailVerify(models.Model):
    email = models.EmailField()
    otp = models.IntegerField(default=0)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" {self.email} - {self.otp}"


class RequestBussinessRegister(models.Model):
    primary_contact_person = models.CharField(max_length=150, blank=True, null=True)
    designation = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField()
    mobile_number = models.CharField(max_length=150, blank=True, null=True)
    bussiness_name = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.email} - {self.designation}"


class OnboardingGstVerify(models.Model):
    request_user = models.ForeignKey(RequestBussinessRegister, on_delete=models.CASCADE)
    gst_number = models.CharField(max_length=50, blank=True, null=True, unique=True)

    date_of_establishment = models.DateField(blank=True, null=True)
    pancard_no = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.gst_number}"


class OnboardingBussinessDetails(models.Model):
    onboarding_gst_verify = models.OneToOneField(
        OnboardingGstVerify, on_delete=models.CASCADE
    )
    first_company_type = models.CharField(max_length=100, blank=True, null=True)
    industry_type = models.CharField(max_length=100, blank=True, null=True)
    website_link = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.first_company_type} - {self.website_link}"


# class OnboardingAlternativePersonDetails(models.Model):
#     onboarding_bussiness_details = models.OneToOneField(
#         OnboardingBussinessDetails,
#         on_delete=models.CASCADE,
#         blank=True,  
#         null=True    
#     )
#     alternative_person_name = models.CharField(max_length=256, blank=True, null=True)
#     alternative_designation = models.CharField(max_length=256, blank=True, null=True)
#     alternative_email = models.CharField(max_length=256, blank=True, null=True)
#     alternative_mobile = models.CharField(max_length=13, null=True, blank=True)

#     def __str__(self):
#         return f"{self.alternative_person_name}"


class OnboardingBankDetails(models.Model):
    # onboarding_alternative_perDetails = models.OneToOneField(
    #     OnboardingBussinessDetails, on_delete=models.CASCADE
    # )
    onboarding_bussiness_details = models.OneToOneField(
        OnboardingBussinessDetails,
        on_delete=models.CASCADE,
        blank=True,  # Allows this field to be blank in forms and admin panels
        null=True    # Allows this field to be null in the database
    )
    upload_pan = models.ImageField(upload_to="Onboarding/", blank=True, null=True)
    upload_gst = models.ImageField(upload_to="Onboarding/", blank=True, null=True)
    certificate_of_corporation = models.ImageField(
        upload_to="Onboarding/", blank=True, null=True
    )
    msme = models.ImageField(upload_to="Onboarding/", blank=True, null=True)
    authorization_letter = models.ImageField(
        upload_to="Onboarding/", blank=True, null=True
    )
    aadhar = models.ImageField(upload_to="Onboarding/", blank=True, null=True)

    # def __str__(self):
    #     return f"{self.}"


class OnboardingCommunication(models.Model):
    onboarding_bank_details = models.OneToOneField(
        OnboardingBankDetails, on_delete=models.CASCADE
    )
    communication_postal_code = models.CharField(max_length=10, null=True, blank=True)
    communication_country = models.CharField(max_length=256, null=True, blank=True)
    communication_state = models.CharField(max_length=256, blank=True, null=True)
    communication_city = models.CharField(max_length=256, blank=True, null=True)
    communication_address = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.communication_postal_code}"


class OnboardingRegisteredAddress(models.Model):
    onboarding_comm_details = models.OneToOneField(
        OnboardingCommunication, on_delete=models.CASCADE
    )
    reg_postal_code = models.CharField(max_length=10, null=True, blank=True)
    reg_country = models.CharField(max_length=256, null=True, blank=True)
    reg_state = models.CharField(max_length=256, blank=True, null=True)
    reg_city = models.CharField(max_length=256, blank=True, null=True)
    reg_address = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.reg_postal_code}"

class WarehouseAddress(models.Model):
    onboarding_reg_details = models.OneToOneField(
        OnboardingRegisteredAddress, on_delete=models.CASCADE
    )
    warehouse_postal_code = models.CharField(max_length=10, null=True, blank=True)
    warehouse_country = models.CharField(max_length=256, null=True, blank=True)
    warehouse_state = models.CharField(max_length=256, blank=True, null=True)
    warehouse_city = models.CharField(max_length=256, blank=True, null=True)
    warehouse_address = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.warehouse_postal_code}"
class OutletAddress(models.Model):
    onboarding_warehouse_details = models.OneToOneField(
        WarehouseAddress, on_delete=models.CASCADE
    )
    outlet_postal_code = models.CharField(max_length=10, null=True, blank=True)
    outlet_country = models.CharField(max_length=256, null=True, blank=True)
    outlet_state = models.CharField(max_length=256, blank=True, null=True)
    outlet_city = models.CharField(max_length=256, blank=True, null=True)
    outlet_address = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return f"{self.outlet_postal_code}"


ClientRequestDetails_CHOICES = [
    ("Requested", "Requested"),
    ("Accepted", "Accepted"),
    ("Rejected", "Rejected"),
    ("Hold", "Hold"),
]


class ClientRequestDetails(models.Model):
    request_user = models.ForeignKey(RequestBussinessRegister, on_delete=models.CASCADE)
    onboarding_gst_verify = models.OneToOneField(
        OnboardingGstVerify, on_delete=models.CASCADE
    )
    onboarding_bussiness_details = models.OneToOneField(
        OnboardingBussinessDetails, on_delete=models.CASCADE
    )
    # onboarding_alternative_perDetails = models.OneToOneField(
    #     OnboardingAlternativePersonDetails, on_delete=models.CASCADE
    # )
    onboarding_bank_details = models.OneToOneField(
        OnboardingBankDetails, on_delete=models.CASCADE, null=True, blank=True
    )
    onboarding_reg_ad = models.OneToOneField(
        OnboardingRegisteredAddress, on_delete=models.CASCADE, null=True, blank=True
    )
    onboarding_comm_ad = models.OneToOneField(
        OnboardingCommunication, on_delete=models.CASCADE, null=True, blank=True
    )
    onboarding_Warehouse_ad = models.OneToOneField(
        WarehouseAddress, on_delete=models.CASCADE, null=True, blank=True
    )
    onboarding_OutletAddress_ad = models.OneToOneField(
        OutletAddress, on_delete=models.CASCADE, null=True, blank=True
    )
    status = models.CharField(
        max_length=10, choices=ClientRequestDetails_CHOICES, default="Requested"
    )
    created_at = models.DateTimeField(auto_now_add=True)


class UniqueStrings(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="use"
    )
    unique_string = models.CharField(max_length=100)
    digit = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.user}"


@receiver(post_save, sender=User)
def generate_unique_string(sender, instance, created, **kwargs):
    if created:
        current_year = datetime.now().year
        prefix = "OUB" + str(current_year)
        existing_strings = UniqueStrings.objects.filter(
            unique_string__startswith=prefix
        )
        new_unique_string = UniqueStrings.objects.create(user=instance)
        if existing_strings.exists():

            last_string = existing_strings.aggregate(max_digit=Max("digit"))[
                "max_digit"
            ]
            new_string = prefix + str(last_string + 1)
            new_unique_string.digit = int(last_string + 1)
        else:

            new_string = prefix + "1"
            new_unique_string.digit = 1
        new_unique_string.unique_string = new_string
        new_unique_string.save()


class ProductUploadSuccesLog(models.Model):
    upload_date = models.DateTimeField(auto_now_add=True)
    upload_count = models.PositiveIntegerField(blank=True, null=True)


class IntermediateProductTableSucces(models.Model):
    log_date_conn = models.ForeignKey(
        ProductUploadSuccesLog, on_delete=models.CASCADE, related_name="log"
    )
    upc = models.CharField(max_length=254, blank=True, null=True)
    hsn_code = models.CharField(max_length=254, blank=True, null=True)
    title = models.CharField(max_length=254, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    Specification = models.TextField(max_length=254, blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    product_type = models.CharField(max_length=254, blank=True, null=True)
    is_public = models.CharField(max_length=254, blank=True, null=True)
    is_discountable = models.CharField(max_length=254, blank=True, null=True)
    best_seller = models.CharField(max_length=100, blank=True, null=True)
    standard_rate = models.CharField(max_length=254, blank=True, null=True)
    num_in_stock = models.CharField(max_length=100, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    first_category = models.CharField(max_length=254, blank=True, null=True)
    attributes = models.TextField(blank=True, null=True)
    Parent_UPC = models.CharField(max_length=254, blank=True, null=True)
    structure = models.CharField(max_length=100, blank=True, null=True)
    recommended_products = models.TextField(blank=True, null=True)
    length = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    supplier = models.CharField(max_length=254, blank=True, null=True)
    low_stock_threshold = models.CharField(max_length=254, blank=True, null=True)
    mrp = models.IntegerField(blank=True, null=True)
    discount = models.IntegerField(blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    gst_rate = models.CharField(max_length=254, blank=True, null=True)


class ProductUploadErrorLog(models.Model):
    upload_date = models.DateTimeField(auto_now_add=True)
    upload_count = models.PositiveIntegerField(blank=True, null=True)


class IntermediateProductTableError(models.Model):
    log_date_conn = models.ForeignKey(
        ProductUploadErrorLog, on_delete=models.CASCADE, related_name="log"
    )
    upc = models.CharField(max_length=254, blank=True, null=True)
    hsn_code = models.CharField(max_length=254, blank=True, null=True)
    title = models.CharField(max_length=254, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    Specification = models.TextField(max_length=254, blank=True, null=True)
    image = models.TextField(blank=True, null=True)
    product_type = models.CharField(max_length=254, blank=True, null=True)
    is_public = models.CharField(max_length=254, blank=True, null=True)
    is_discountable = models.CharField(max_length=254, blank=True, null=True)
    best_seller = models.CharField(max_length=100, blank=True, null=True)
    standard_rate = models.CharField(max_length=254, blank=True, null=True)
    num_in_stock = models.CharField(max_length=100, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    first_category = models.CharField(max_length=254, blank=True, null=True)
    attributes = models.TextField(blank=True, null=True)
    Parent_UPC = models.CharField(max_length=254, blank=True, null=True)
    structure = models.CharField(max_length=100, blank=True, null=True)
    recommended_products = models.TextField(blank=True, null=True)
    length = models.IntegerField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    supplier = models.CharField(max_length=254, blank=True, null=True)
    low_stock_threshold = models.CharField(max_length=254, blank=True, null=True)
    mrp = models.IntegerField(blank=True, null=True)
    discount = models.IntegerField(blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    gst_rate = models.CharField(max_length=254, blank=True, null=True)
    error = models.TextField(blank=True, null=True)


class UpdateErpstatus(models.Model):
    upc = models.CharField(max_length=100)
    update_erp = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.upc}"


class GetHelpOnHomePage(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    image = models.ImageField(upload_to="GetHelpImage/", blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.phone_number} - {self.message}"
