from django.apps import apps
from django.conf import settings

from django.apps import apps
from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from .views import VoucherSetDOwnload, VoucherSetDetailView, VoucherSetSendMailView, VoucherSetCSVFileDownloadView


urlpatterns = [
    path("download/<int:pk>/", VoucherSetDOwnload.as_view()),
    path("detail/<int:pk>/", VoucherSetDetailView.as_view(), name="voucher-detail"),
    path("send_mail/<int:pk>/", VoucherSetSendMailView.as_view()),
    path("CSV-Download/<int:pk>/", VoucherSetCSVFileDownloadView.as_view(), name="CSV-Download"),

]
