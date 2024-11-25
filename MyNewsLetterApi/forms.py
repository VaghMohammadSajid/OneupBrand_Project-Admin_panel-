from django import forms
from django.conf import settings
from django.forms import TextInput
from django.shortcuts import render, redirect
from django.views import View
from tinymce.widgets import TinyMCE

from MyNewsLetterApi.models import SubscriberModel, TemplateModel, SendNewsletterModel


class SubscriberForm(forms.ModelForm):
    class Meta:
        model = SubscriberModel
        fields = ["full_name", "email", "status", "current_date"]


class TemplateForm(forms.ModelForm):
    class Meta:
        model = TemplateModel
        fields = ["subject", "message", "status"]  # 'from_email' , 'reply_to_email',

        STATUS_CHOICES = [
            ("Active", "Active"),
            ("Inactive", "Inactive"),
        ]

        widgets = {
            # 'from_email': forms.EmailInput(
            #     attrs={'class': 'form-control', 'placeholder': 'From Email', 'required': True, 'value': settings.EMAIL_HOST_USER,'readonly': 'readonly'}),
            # 'reply_to_email': forms.EmailInput(
            #     attrs={'class': 'form-control', 'placeholder': 'Replay To Email', 'required': True}),
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control mt-1",
                    "placeholder": "Enter Subject",
                    "required": True,
                }
            ),
            "message": TinyMCE(
                attrs={"class": "form-control", "style": "height:300px;"}
            ),
            "status": forms.Select(
                attrs={"class": "form-control", "required": True},
                choices=STATUS_CHOICES,
            ),
        }


class SendNewsletterForm(forms.ModelForm):
    class Meta:
        model = SendNewsletterModel
        fields = ["template", "status"]

    STATUS_CHOICES = [
        ("All", "Send To All"),
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    template = forms.ModelChoiceField(
        queryset=TemplateModel.objects.filter(
            status="Active"
        ),  # Replace YourTemplateModel with your actual template model
        empty_label="Select a template",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    status = forms.ChoiceField(
        widget=forms.Select(
            choices=STATUS_CHOICES, attrs={"class": "form-control", "required": True}
        ),
        label="Subscriber Status",
    )

    def __init__(self, *args, **kwargs):
        super(SendNewsletterForm, self).__init__(*args, **kwargs)
        self.fields["status"].choices = self.STATUS_CHOICES
