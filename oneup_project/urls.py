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
import debug_toolbar


urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    # The Django admin is not officially supported; expect breakage.
    # Nonetheless, it's often useful for debugging.
    path("admin/", admin.site.urls),
    path("catalogue/", include("redirect_to_catelogue.urls")),
    path("", include(apps.get_app_config("oscar").urls[0])),
    path("api/", include("oscarapi.urls")),
    path("useraccount/", include("useraccount.urls")),
    path("homepageapi/", include("homepageapi.urls")),
    path("my_api/", include("mycustomapi.urls")),
    path("bannermanage/", include("bannermanagement.urls")),
    path("discounts/", include("DiscountManagement.urls")),
    path("MyNewsLetterApi/", include("MyNewsLetterApi.urls")),
    path("order/", include("apps.order.urls"), name="order"),
    path("tinymce/", include("tinymce.urls")),
    path("cartapi/", include("cart_api.urls")),
    path("role/", include("role_permission.urls")),
    path("ship/", include("fshipapi.urls")),
    path("voucher/", include("apps.dashboard.vouchers.urls")),
    path("sync-details/", include("sync_data_erp.urls")),
    path("voucher_type/", include("apps.dashboard.offers.urls")),
    path("wallet/", include("wallet.urls")),
    path("credit/", include("credit.urls")),
    path("whatsapp/", include("whatsapp.urls")),
    path("webhooks/", include("webhooks.urls")),
    path("report/", include("report.urls")),
    path("task/", include("task_runner.urls")),
     path('__debug__/', include(debug_toolbar.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
