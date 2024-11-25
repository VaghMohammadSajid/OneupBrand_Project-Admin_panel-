# discounts/urls.py
from django.urls import path
from .views import apply_discount, CategoryListApi

urlpatterns = [
    path("apply_discount/", apply_discount, name="apply_discount"),
    path("category_list/", CategoryListApi.as_view()),
]
