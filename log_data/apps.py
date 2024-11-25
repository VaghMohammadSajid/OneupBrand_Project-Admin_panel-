from django.apps import AppConfig


class LogDataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "log_data"

    def ready(self):
        import log_data.signals
