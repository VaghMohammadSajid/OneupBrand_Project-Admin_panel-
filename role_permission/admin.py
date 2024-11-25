from django.contrib import admin
from .models import Permissions, Roles,Role

# Register your models here.


admin.site.register(Permissions)
admin.site.register(Roles)
admin.site.register(Role)
