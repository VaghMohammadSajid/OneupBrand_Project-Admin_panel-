# serializers.py
from rest_framework import serializers
from .models import SubscriberModel, TemplateModel, SendNewsletterModel


class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberModel
        fields = ["full_name", "email", "status"]


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateModel
        fields = "__all__"


class SendNewsletterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SendNewsletterModel
        fields = "__all__"
