from django.db import models

# Create your models here.
from django.core.mail import send_mail
from django.db import models
from django.conf import settings
from tinymce.models import HTMLField


# Create your models here.


class SubscriberModel(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    current_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-current_date"]

    def __str__(self):
        return self.full_name


class TemplateModel(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    from_email = models.EmailField()
    reply_to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = HTMLField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Active")
    current_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-current_date"]

    def __str__(self):
        return self.subject


class SendNewsletterModel(models.Model):
    STATUS_CHOICES = [
        ("All", "Send To All"),
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    template = models.ForeignKey(TemplateModel, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def send_newsletters(self):
        subscribers = SubscriberModel.objects.all()

        if self.status == "All":
            # Send to all subscribers
            for subscriber in subscribers:
                self.send_newsletter(subscriber)
        else:
            # Send to subscribers based on the selected status
            filtered_subscribers = subscribers.filter(status=self.status)
            for subscriber in filtered_subscribers:
                self.send_newsletter(subscriber)

    def send_newsletter(self, subscriber):
        subject = self.template.subject
        message = self.template.message

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [subscriber.email],
            fail_silently=False,
            html_message=message,
        )

    def __str__(self):
        return f"{self.template}"
