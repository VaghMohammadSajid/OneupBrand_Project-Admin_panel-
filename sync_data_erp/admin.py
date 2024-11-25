from django.contrib import admin
from .models import FailedOrder, StockSyncReport

# Register your models here.

admin.site.register(FailedOrder)
admin.site.register(StockSyncReport)
