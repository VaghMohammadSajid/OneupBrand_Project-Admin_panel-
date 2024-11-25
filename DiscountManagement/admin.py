from django.contrib import admin

# Register your models here.
from .models import ProxyClassForRange
from .models import VoucherAllocationBYLine


admin.site.register(ProxyClassForRange)
admin.site.register(VoucherAllocationBYLine)
