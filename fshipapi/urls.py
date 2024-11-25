from django.urls import include, path
from .views import (
    CheckAdd,
    ShipAvailableAPi,
    RateCalcOnPdpPageAPi,
    RateCalcOnPdpPageAPi,
    ShipPriceCalcAPI,
    OrderTrackNow,
)

urlpatterns = [
    path("get-add/", CheckAdd.as_view()),
    path("check-available/", ShipAvailableAPi.as_view()),
    path("get_single_product_price/", RateCalcOnPdpPageAPi.as_view()),
    path("get_price/", ShipPriceCalcAPI.as_view()),
    path("track-order-now/", OrderTrackNow.as_view()),
]
