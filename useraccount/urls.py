from django.urls import path

from .views import (
    ClientUser,
    AdminUser,
    GetALLVoucherCode,
    GetVouchersView,
    LoginView,
    vouchercodeverify,
    CustomerLoginView,
    SentOtpForMobile,
    VerifyRegistrations,
    ClientUserListView,
    AdminUserListView,
    EditClientView,
    UserInfoAPIview,
    ForgotPasswordView,
    ForgotPasswordViewByCustomer,
    ResetPasswordView,
    OTPVerifyView,
    ContactUsAPIView,
    DeleteClientView,
    EditAdminView,
    DeleteAdminView,
    ContactListView,
    GetHelpOnHomePageAPIView,
    GetHelpOnHomePageView,
    GetHelpOnHomePageDeleteView,
    GetHelpOnHomePageDetailsView,
    CleintREgisterTotalAPi,
)

from .views import (
    VerifyOTPForOrder,
    SentOtpForMobileTrackOrder,
    VoucherCheck,
    ClientEmailVerifyApiView,
    ClientOtpVerifyApiView,
    OnboardingStepone,
    OnboardingSteptwo,
    OnboardingStepthree,
    OnboardingStepfour,
    UserAlreadyExistsSignup,
    ClientRegisterRequest,
    ClientOnboardingStepOne,
    ClientOnboardingStepTwo,
    ClientOnboardingStepThree,
    ClientOnboardingStepFour,
    ClientOnboardingStepFive,
    ClientOnboardingStepSix,
    ClientOnboardingStepSeven,
    ClientRequestDetailsList,
    ClientRequestDetailsUpdate,
    ClientRequestDetailsAction,
    ClientRequestDetailsSave,
    CheckGstAlreadyExists,
    CheckEmailAlreadyExists,
    VoucherLogin,
    ResetPassword,SendMail
)
from .import_erp import (
    upload_page,
    OrderListView,
    send_data_to_erp,
    get_child_data,
    StockIntegrations,
    OrderIntegrations,
    SendJsonForProductUploadApi,
)

from .bulk_api import bulk_product, update_stock_records
from . import import_erp
from .upload_products import bulk_product as b, SendStatus
from .two_table import CreateTwoTablesApi
from . import views


urlpatterns = [
    path("ClientUser/", ClientUser.as_view(), name="ClientUser"),
    path(
        "ClientRequestList/",
        ClientRequestDetailsList.as_view(),
        name="ClientRequestList",
    ),
    path(
        "ClientRequestUpdate/<int:pk>/",
        ClientRequestDetailsUpdate.as_view(),
        name="ClientRequestUpdate",
    ),
    path(
        "ClientRequestDetailsAction/<int:pk>/",
        ClientRequestDetailsAction.as_view(),
        name="ClientRequestDetailsAction",
    ),
    path(
        "ClientRequestDetailsSave/<int:pk>/",
        ClientRequestDetailsSave.as_view(),
        name="ClientRequestDetailsSave",
    ),
    path(
        "download_client_request_log/",
        views.download_client_request_log,
        name="download_client_request_log",
    ),
    path("edit-client/<int:pk>/", EditClientView.as_view(), name="edit-client"),
    path("delete-client/<int:pk>/", DeleteClientView.as_view(), name="delete-client"),
    path("AdminUser/", AdminUser.as_view(), name="AdminUser"),
    path("edit-admin/<int:pk>/", EditAdminView.as_view(), name="edit-admin"),
    path("delete-admin/<int:pk>/", DeleteAdminView.as_view(), name="delete-admin"),
    path("LoginView/", LoginView.as_view(), name="LoginView"),
    path("vouchercodeverify/", vouchercodeverify.as_view(), name="vouchercodeverify"),
    path("CustomerLoginView/", CustomerLoginView.as_view(), name="CustomerLoginView"),
    path("SentOtpForMobile/", SentOtpForMobile.as_view(), name="SentOtpForMobile"),
    path(
        "VerifyRegistrations/",
        VerifyRegistrations.as_view(),
        name="VerifyRegistrations",
    ),
    path("client-list/", ClientUserListView.as_view(), name="client-list"),
    path("admin-list/", AdminUserListView.as_view(), name="admin-list"),
    path("edit-client/<int:pk>/", EditClientView.as_view(), name="edit-client"),
    path("clientinfo/", UserInfoAPIview.as_view(), name="clientinfo-api"),
    path("erp-data/", b, name="products_from_erp"),
    path("upload/", upload_page, name="upload"),
    path("GetALLVoucherCode/", GetALLVoucherCode.as_view(), name="GetALLVoucherCode"),
    path("GetVouchersView/", GetVouchersView.as_view(), name="GetVouchersView"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path(
        "reset-password/<int:pk>/", ResetPasswordView.as_view(), name="reset-password"
    ),
    path("verify-OTP/<int:pk>/", OTPVerifyView.as_view(), name="verify-OTP"),
    path("import_data/", b, name="bulk_product_upload"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="reset-password"),
    path(
        "forgot-password-customer/<int:pk>/",
        ForgotPasswordViewByCustomer.as_view(),
        name="forgot-password-customer",
    ),
    path("erp_order/", OrderListView.as_view(), name="erp-order-list"),
    path("demo_erp/", send_data_to_erp, name="demoerp"),
    path("update-stock-record/", update_stock_records, name="update-stock-record"),
    path("contact/", ContactUsAPIView.as_view(), name="contact-us"),
    path("contact-list/", ContactListView.as_view(), name="contact-list"),
    path("order-list/", VerifyOTPForOrder.as_view()),
    path("track-order-sms/", SentOtpForMobileTrackOrder.as_view()),
    path("check-voucher/", VoucherCheck.as_view()),
    path("child/<int:id>/", get_child_data),
    path(
        "client-register-request/",
        ClientRegisterRequest.as_view(),
        name="client-register-request",
    ),
    path(
        "Stock-Integrations-list/",
        StockIntegrations.as_view(),
        name="Stock-Integrations-list",
    ),
    path(
        "Order-Integrations-list/",
        OrderIntegrations.as_view(),
        name="Order-Integrations-list",
    ),
    path(
        "client-already-verify/",
        UserAlreadyExistsSignup.as_view(),
        name="client-already-verify",
    ),
    path(
        "client-email-verify/",
        ClientEmailVerifyApiView.as_view(),
        name="client-email-verify",
    ),
    path(
        "client-otp-verify/", ClientOtpVerifyApiView.as_view(), name="client-otp-verify"
    ),
    path("product_upload_data/", SendJsonForProductUploadApi.as_view()),
    path("onboardingGstVerify/", OnboardingStepone.as_view()),
    path("onboarding-bussiness-details/", OnboardingSteptwo.as_view()),
    path("onboarding-alternative-person-details/", OnboardingStepthree.as_view()),
    path("onboarding-bank-details/", OnboardingStepfour.as_view()),
    # add new client in admin site
    path(
        "ClientOnboardingStepOne/",
        ClientOnboardingStepOne.as_view(),
        name="ClientOnboardingStepOne",
    ),
    path(
        "ClientOnboardingStepTwo/",
        ClientOnboardingStepTwo.as_view(),
        name="ClientOnboardingStepTwo",
    ),
    path(
        "ClientOnboardingStepThree/",
        ClientOnboardingStepThree.as_view(),
        name="ClientOnboardingStepThree",
    ),
    path(
        "ClientOnboardingStepFour/",
        ClientOnboardingStepFour.as_view(),
        name="ClientOnboardingStepFour",
    ),
    path(
        "ClientOnboardingStepFive/",
        ClientOnboardingStepFive.as_view(),
        name="ClientOnboardingStepFive",
    ),
    path(
        "ClientOnboardingStepSix/",
        ClientOnboardingStepSix.as_view(),
        name="ClientOnboardingStepSix",
    ),
    path(
        "ClientOnboardingStepSeven/",
        ClientOnboardingStepSeven.as_view(),
        name="ClientOnboardingStepSeven",
    ),

    path("update-status/", CreateTwoTablesApi.as_view()),
    path("send-erp-status/", SendStatus.as_view()),
    # Get Help on Front Page
    path(
        "get-help/",
        GetHelpOnHomePageAPIView.as_view(),
        name="get-help",
    ),
    path("get-help-list/", GetHelpOnHomePageView.as_view(), name="get-help-list"),
    path(
        "delete-get_help/<int:pk>/",
        GetHelpOnHomePageDeleteView.as_view(),
        name="delete-get_help",
    ),
    path(
        "details-get_help/<int:pk>/",
        GetHelpOnHomePageDetailsView.as_view(),
        name="details-get_help",
    ),
    path("Onboarding_final", CleintREgisterTotalAPi.as_view(), name="details-get_help"),
    path(
        "check-gst-onboarding/",
        CheckGstAlreadyExists.as_view(),
        name="check-gst-onboarding",
    ),
    path(
        "check-email-onboarding/",
        CheckEmailAlreadyExists.as_view(),
        name="check-email-onboarding",
    ),
    path(
        "voucher-login-with-details/",
        VoucherLogin.as_view(),
        name="check-email-onboarding",
    ),
    path(
        "change_password",
        ResetPassword.as_view(),
       
    ),
    path('send-mail/',SendMail.as_view()),
]
