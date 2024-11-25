# from oscar.apps.basket.admin import *
from django.contrib import admin
from .models import Basket
from .models import ShippinCharge

admin.site.register(Basket)


admin.site.register(ShippinCharge)
