from django.dispatch import Signal

oscarapi_post_checkout = Signal(["order", "user", "request", "response"])
