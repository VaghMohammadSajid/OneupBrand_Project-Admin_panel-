from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect


def redirect_to_dashboard(request, path=None):
    if request.user:
        return redirect("/dashboard")
    else:
        return redirect("/dashboard")
