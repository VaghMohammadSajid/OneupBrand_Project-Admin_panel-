from django.shortcuts import render

# Create your views here.
# Create your views here.
# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.views import View
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import SubscriberForm, TemplateForm, SendNewsletterForm
from .models import SubscriberModel, TemplateModel, SendNewsletterModel
from .serializers import SubscriberSerializer
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# Start SubscriberAPIView, Subscriber Listing , Action(Active Or Inactive) and Delete
class SubscriberAPIView(APIView):

    def post(self, request, *args, **kwargs):
        # Handle form submission for adding new subscribers
        subscriber_serializers = SubscriberSerializer(data=request.data)

        if subscriber_serializers.is_valid():
            subscriber_serializers.validated_data["current_date"] = timezone.now()
            subscriber_serializers.save()

            return Response({"message": "Subscriber added successfully"})
        else:
            return Response({"message": "Email Already Exist."})


class SubscriberListView(View):
    template_name = "newsletter/news_list.html"

    def get(self, request, *args, **kwargs):
        subscriber_form = SubscriberForm()
        newsletter_subscribers = SubscriberModel.objects.all()
        return render(
            request,
            self.template_name,
            {
                "newsletter_subscribers": newsletter_subscribers,
                "subscriber_form": subscriber_form,
            },
        )

    def post(self, request, *args, **kwargs):
        subscriber_form = SubscriberForm(request.POST)
        email = request.POST.get("email")
        searched_email = email
        if email:
            newsletter_subscribers = SubscriberModel.objects.filter(
                email__icontains=email
            )
        else:
            newsletter_subscribers = SubscriberModel.objects.all()
        return render(
            request,
            self.template_name,
            {
                "newsletter_subscribers": newsletter_subscribers,
                "subscriber_form": subscriber_form,
                "searched_email": searched_email,
            },
        )


class SubscriberActionView(View):
    def post(self, request, subscriber_id):
        # Retrieve the Template
        subscribe = get_object_or_404(SubscriberModel, pk=subscriber_id)

        # Toggle the status
        subscribe.status = "Active" if subscribe.status == "Inactive" else "Inactive"
        subscribe.save()
        print(subscribe.status)
        messages.success(
            request,
            f'SuccessFully, Subscriber "{subscribe.full_name}" is "{subscribe.status}" .',
        )

        # Redirect to the subscriber list view
        return redirect("subscriber-list")


class SubscriberDeleteView(View):
    def get(self, request, subscriber_id):
        # Handle subscriber deletion
        subscriber = get_object_or_404(SubscriberModel, pk=subscriber_id)
        subscriber.delete()
        messages.success(
            request, f'Successfully,"{subscriber.full_name}" Template was deleted.'
        )
        return redirect("subscriber-list")

    # Start Template Create, Listing , Action(Active Or Inactive) , Delete and Edit


class CreateTemplateView(View):
    template_name = "newsletter/CreateTemplate.html"

    def get(self, request):
        create_template_form = TemplateForm()
        create_template_form.replay_to_email = settings.EMAIL_HOST_USER
        return render(
            request, self.template_name, {"create_template_form": create_template_form}
        )

    def post(self, request):
        # Handle form submission for creating a new newsletter template
        create_template_form = TemplateForm(request.POST)
        if create_template_form.is_valid():
            create_template_form.instance.current_date = timezone.now()
            create_template_form.save()
            messages.success(request, "Template created successfully.")
            return redirect(reverse("create-template"))
        else:
            return redirect(reverse("create-template"))


class ManageNewsletterTemplate(View):
    template_name = "newsletter/Manage_Newsletter_Template.html"

    def get(self, request):
        manage_template_form = TemplateForm()
        newsletter_template_subscribers = TemplateModel.objects.all()

        return render(
            request,
            self.template_name,
            {
                "newsletter_template_subscribers": newsletter_template_subscribers,
                "manage_template_form": manage_template_form,
            },
        )


class TemplateActionView(View):
    def post(self, request, template_id):
        # Retrieve the Template object
        template = get_object_or_404(TemplateModel, pk=template_id)

        # Toggle the status
        template.status = "Active" if template.status == "Inactive" else "Inactive"
        template.save()
        messages.success(
            request,
            f'Successfully,"{template.subject}" Template was "{template.status}".',
        )

        # Redirect to the Template list view
        return redirect("Manage-NewsLetter-Template")


class DeleteTemplateView(View):
    def get(self, request, template_id):
        template = get_object_or_404(TemplateModel, pk=template_id)
        template.delete()
        messages.success(
            request, f'Successfully,"{template.subject}" Template was deleted.'
        )

        # Redirect to the same page after deletion
        return redirect("Manage-NewsLetter-Template")


class EditTemplateView(View):
    template_name = "newsletter/EditTemplate.html"

    def get(self, request, template_id):
        # Use get_object_or_404 for safety
        template_form = TemplateForm()
        template_user = get_object_or_404(TemplateModel, pk=template_id)
        return render(
            request,
            self.template_name,
            {"template_user": template_user, "template_form": template_form},
        )

    def post(self, request, template_id):
        # Use get_object_or_404 for safety
        template_form = TemplateForm()
        template_user = get_object_or_404(TemplateModel, pk=template_id)

        if request.method == "POST":
            # Update fields based on POST data
            template_user.subject = request.POST.get("subject")
            template_user.message = request.POST.get("message")
            template_user.status = request.POST.get("status")

            # update the current date
            template_user.current_date = timezone.now()

            # Save the changes
            template_user.save()

            # Redirect to the template list page or any other page as needed
            messages.success(
                self.request,
                _(f"""Template '{template_user.subject}' updated successfully!"""),
            )
            return redirect("Manage-NewsLetter-Template")

        return render(
            request,
            self.template_name,
            {"template_user": template_user, "template_form": template_form},
        )


# Start Newsletter
class SendNewsletterView(View):
    template_name = "newsletter/send_newsletter.html"

    def get(self, request):
        # Render the form to send a new newsletter
        SendNewsletter_form = SendNewsletterForm()
        return render(
            request,
            self.template_name,
            {
                "SendNewsletter_form": SendNewsletter_form,
            },
        )

    def post(self, request):
        # Handle form submission for sending a new newsletter
        SendNewsletter_form = SendNewsletterForm(request.POST)
        if SendNewsletter_form.is_valid():
            status = SendNewsletter_form.cleaned_data["status"]
            template = SendNewsletter_form.cleaned_data["template"]

            subscriber_status = SubscriberModel.objects.filter(status=status)
            if subscriber_status:
                send_newsletter = SendNewsletterModel(template=template, status=status)
                send_newsletter.save()
                try:
                    send_newsletter.send_newsletters()
                except Exception as e:
                    messages.error(request, f"An error occurred while sending a email : {e}")
                    return redirect("send-newsletter")

                messages.success(request, "Newsletters sent successfully.")
                return redirect("send-newsletter")
            else:
                messages.error(request, "No Subscriber is " + status)
                return redirect("send-newsletter")
        else:
            messages.error(request, "Something went wrong. Please try again.")
            return render(
                request,
                self.template_name,
                {"SendNewsletter_form": SendNewsletter_form},
            )
