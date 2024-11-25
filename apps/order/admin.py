from oscar.apps.order.admin import *
from .models import Razorpay, StatusReprotOrderErpToAdmin, OrderJson
from django.contrib import admin


admin.site.register(Razorpay)
admin.site.register(StatusReprotOrderErpToAdmin)
admin.site.register(OrderJson)
