from django.apps import apps
from django.conf import settings

from django.apps import apps
from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from .views import OrderDetail, OrderListViewpadf, OrderListfullView


urlpatterns = [
    path("detail/<str:number>/", OrderDetail.as_view()),
    path("downloadpdf", OrderListViewpadf.as_view()),
    path("full-orders", OrderListfullView.as_view(), name="full-orders"),
]
