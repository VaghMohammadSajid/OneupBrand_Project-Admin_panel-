from django.contrib import admin

from MyNewsLetterApi.models import SubscriberModel, TemplateModel, SendNewsletterModel

# Register your models here.

admin.site.register(SubscriberModel)
admin.site.register(TemplateModel)
admin.site.register(SendNewsletterModel)
