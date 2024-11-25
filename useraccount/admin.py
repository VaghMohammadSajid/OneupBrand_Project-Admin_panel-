from django.contrib import admin

# Register your models here.

# Register your models here.
from .models import (
    UserProfile,
    UserAuthTokens,
    ClientDetails,
    Contact,
    VoucherUser,
    VocherLoginConnect,
    UploadProductJSon,
    IntermediateProductTableChild,
    ClientEmailVerify,
    RequestBussinessRegister,
    OnboardingBussinessDetails,
    OnboardingBankDetails,
    OnboardingCommunication,
    OnboardingRegisteredAddress,
    # OnboardingAlternativePersonDetails,
    OnboardingGstVerify,
    WarehouseAddress,
    OutletAddress,
    ClientRequestDetails,
    UpdateErpstatus,
    GetHelpOnHomePage,
    UploadProductJSon
)
from .models import UniqueStrings
from .two_table import (
    ProductUploadErrorLog,
    ProductUploadSuccesLog,
    IntermediateProductTableError,
    IntermediateProductTableSucces,
)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "mobile_number",
        "otp",
        "otp_verify",
        "added_on",
        "updated_on",
    ]


class UserAuthTokensAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_info",
        "access_token",
        "refresh_token",
        "added_on",
        "updated_on",
    ]


class CustomStockRecordAdmin(admin.ModelAdmin):
    list_display = (
        "partner",
        "product",
        "partner_sku",
        "price",
        "mrp",
        "discount",
        "discount_type",
    )


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserAuthTokens, UserAuthTokensAdmin)
admin.site.register(ClientDetails)
admin.site.register(Contact)
admin.site.register(VoucherUser)
admin.site.register(VocherLoginConnect)
admin.site.register(UploadProductJSon)
admin.site.register(IntermediateProductTableChild)
admin.site.register(ClientEmailVerify)
admin.site.register(RequestBussinessRegister)
admin.site.register(OnboardingGstVerify)
admin.site.register(OnboardingBussinessDetails)
# admin.site.register(OnboardingAlternativePersonDetails)
admin.site.register(OnboardingBankDetails)
admin.site.register(OnboardingCommunication)
admin.site.register(OnboardingRegisteredAddress)
admin.site.register(WarehouseAddress)
admin.site.register(OutletAddress)
admin.site.register(ClientRequestDetails)
admin.site.register(UniqueStrings)
admin.site.register(IntermediateProductTableSucces)
admin.site.register(IntermediateProductTableError)
admin.site.register(ProductUploadSuccesLog)
admin.site.register(ProductUploadErrorLog)
admin.site.register(UpdateErpstatus)
admin.site.register(GetHelpOnHomePage)
