from django.contrib import admin

# Register your models here.
from .models import Credit, CreditHistory,OtpForCredit

admin.site.register(Credit)
admin.site.register(CreditHistory)
admin.site.register(OtpForCredit)
