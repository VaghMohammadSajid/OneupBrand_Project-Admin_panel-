from django.urls import path

from apps.dashboard.offers import views

urlpatterns = [
    path("add_vaoucher_type/", views.vouchercreateview, name="vouchercreateview"),
    path("get-brand/", views.GetBrand.as_view()),
    path("get-brand-cate/", views.GetBrandOnCate.as_view()),
    path("edit-offer/<int:id>", views.edit_offer),
]
