from django.urls import path

from MyNewsLetterApi.views import (
    SubscriberAPIView,
    SubscriberListView,
    SubscriberActionView,
    SubscriberDeleteView,
    ManageNewsletterTemplate,
    CreateTemplateView,
    TemplateActionView,
    DeleteTemplateView,
    EditTemplateView,
    SendNewsletterView,
)

urlpatterns = [
    path("subscriber/", SubscriberAPIView.as_view(), name="subscriber"),
    path("subscriber-list/", SubscriberListView.as_view(), name="subscriber-list"),
    path(
        "toggle-active/<int:subscriber_id>/",
        SubscriberActionView.as_view(),
        name="toggle-active",
    ),
    path(
        "delete-subscriber/<int:subscriber_id>/",
        SubscriberDeleteView.as_view(),
        name="delete-subscriber",
    ),
    path(
        "Manage-NewsLetter-Template/",
        ManageNewsletterTemplate.as_view(),
        name="Manage-NewsLetter-Template",
    ),
    path("create-template/", CreateTemplateView.as_view(), name="create-template"),
    path(
        "template-active/<int:template_id>",
        TemplateActionView.as_view(),
        name="template-active",
    ),
    path(
        "delete-template/<int:template_id>/",
        DeleteTemplateView.as_view(),
        name="delete-template",
    ),
    path(
        "edit-template/<int:template_id>/",
        EditTemplateView.as_view(),
        name="edit-template",
    ),
    path("send-newsletter/", SendNewsletterView.as_view(), name="send-newsletter"),
]
