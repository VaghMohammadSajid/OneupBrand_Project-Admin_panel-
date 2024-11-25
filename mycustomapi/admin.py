from django.contrib import admin

# Register your models here.
from mycustomapi.models import *


# Register your models here.
admin.site.register(ApiKey)

admin.site.register(GSTGroup)
admin.site.register(GSTSetup)
