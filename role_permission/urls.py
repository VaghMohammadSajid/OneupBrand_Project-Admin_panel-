"""
URL configuration for oneup_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path

from .views import render_error_page, change_role, ReadNotificationView,add_role


urlpatterns = [
    # path('role-add',AddRoleView.as_view(),name="add-r"),
    # path('add-url',add_url,name="add-url"),
    path('add-role',add_role,name="add-role"),
    # path('assign-user',assign_user,name="assign-user"),
    path("change-role/", change_role),
    path("error-403-mid", render_error_page),
    path(
        "read-notification/<int:pk>",
        ReadNotificationView.as_view(),
        name="read-notification",
    ),
]
