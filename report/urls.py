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

from django.urls import path

from . import views


urlpatterns = [
    path("error-log", views.product_error_view, name="error-log"),
    path("success-log", views.product_success_view, name="success-log"),
    path("error/list/<int:id>", views.error_product_list),
    path("success/list/<int:id>", views.success_product_list),
    path("download-product-csv", views.download_product_csv),
    path("download_error_log/", views.download_error_log, name="download_error_log"),
    path(
        "download_success_log/", views.download_success_log, name="download_success_log"
    ),
]
