from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, redirect

from django.views import View
from rest_framework import generics

from mycustomapi.serializers.tax import *
from mycustomapi.models import *


class AddGSTSetup(View):
    template_name = "taxes/gstsetup.html"

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            # You may want to add a success message or redirect to a login page
            return redirect("login")
        return render(request, self.template_name, {"form": form})


from django.views import View


class AddGSTGroup(View):
    template_name = "taxes/gst_group.html"

    def get(self, request):

        print("HHHHHHHHHHHHH")

        return render(request, self.template_name)

    def post(self, request):

        print("HEEEEEEEEEEE")

        if request.method == "POST":
            print("TTTTTTTTTTT")
            gst_code = request.post.get("gst_code")
            description = request.post.get("description")
            gst_rate = request.post.get("gst_rate")

            print(gst_rate, "GGGGGGGG")
            print(gst_code, "GGGGGGGGGGGGGGGGGG")
            print(description, "descriptiondescription")


class GSTGroupList(generics.ListCreateAPIView):
    queryset = GSTGroup.objects.all()
    serializer_class = GSTGroupSerializer


class GSTGroupDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = GSTGroup.objects.all()
    serializer_class = GSTGroupSerializer


class GSTSetupList(generics.ListCreateAPIView):
    queryset = GSTSetup.objects.all()
    serializer_class = GSTSetupSerializer


class GSTSetupDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = GSTSetup.objects.all()
    serializer_class = GSTSetupSerializer
