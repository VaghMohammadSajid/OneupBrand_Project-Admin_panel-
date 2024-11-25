from django.apps import AppConfig


class MycustomapiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mycustomapi"

    def ready(self):
        import mycustomapi.signals
