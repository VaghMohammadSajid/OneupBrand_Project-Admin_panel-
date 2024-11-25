"""
URL configuration for oneup_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.apps import apps
from django.conf import settings

from django.apps import apps
from django.urls import include, path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from .views import admin_view, TotalAmountApi, RemoveAmount, credit_history, CreditFlow

from .views import CreditRequestUserApi
from .views import (
    CreditRequestUserList,
    CreditRequestUserDelete,
    CreditHistoryApiView,
    CreditRequestErp,
    CreditHistoryDowloadView,
    CreditotpApi,
    CreditotpVerifyApi,
    CreditApplyCart,
    CartRemoveCredit
)

urlpatterns = [
    path("user-credit/", admin_view, name="credit"),
    path("total_amount/", TotalAmountApi.as_view()),
    path("remove-amount/", RemoveAmount.as_view()),
    path("history/<int:id>/", credit_history),
    path("credit-sync", CreditFlow.as_view()),
    path("credit-sync-erp", CreditFlow.as_view()),
    path(
        "credit-request-user/<int:pk>/",
        CreditRequestUserApi.as_view(),
        name="credit-request-user-get",
    ),
    path(
        "credit-request-user/",
        CreditRequestUserApi.as_view(),
        name="credit-request-user-post",
    ),
    path(
        "credit-requests/",
        CreditRequestUserList.as_view(),
        name="credit-request-user-list",
    ),
    # path('credit-requests/status/<int:pk>/', CreditRequestUserStatusUpdate.as_view(), name='credit-request-user-status'),
    path(
        "credit-requests/delete/<int:pk>/",
        CreditRequestUserDelete.as_view(),
        name="credit-request-user-delete",
    ),
    path("credit-history/", CreditHistoryApiView.as_view(), name="credit-history"),
    path("credit-request-erp/", CreditRequestErp.as_view(), name="credit-request-erp"),
    path("credit-history-csv/", CreditHistoryDowloadView.as_view()),
    path("send-otp/", CreditotpApi.as_view()),
    path("verify-otp/", CreditotpVerifyApi.as_view()),
    path("credit-apply-cart/",CreditApplyCart.as_view()),
    path("credit-remove-cart/",CartRemoveCredit.as_view()),

]
