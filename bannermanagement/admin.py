from django.contrib import admin
from .models import Brand

from .models import (
    Bannermanagement,
    CategoryPromotion,
    CategoryPromotionSet,
    VoucherSet,
    VoucherRequestUser,
)

# Register your models here.

admin.site.register(Bannermanagement)
admin.site.register(CategoryPromotion)
admin.site.register(CategoryPromotionSet)
admin.site.register(VoucherSet)
admin.site.register(VoucherRequestUser)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    pass
