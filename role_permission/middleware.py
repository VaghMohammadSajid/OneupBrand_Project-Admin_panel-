from .models import Permissions, Roles
from django.http import HttpResponseRedirect
from django.urls import resolve
import re
import logging
import threading


logger = logging.getLogger(__name__)


class CheckRequestURLMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        clean_url = re.sub(r"<[^>]+>", "", resolve(request.path_info).route)
        print(clean_url, "welcome")
        print(request.method.lower())
        method = request.method.lower()
        try:
            role = Roles.objects.get(user=request.user)
            search_url = method + '/' + clean_url
            
            if search_url in role.role.permission_denied.all().values_list("non_permitted_url",flat=True):
                return HttpResponseRedirect("/role/error-403-mid")
            
        except Exception as e:
            print(e)
            print("errorr")
        print(request.user.id)

        
        response = self.get_response(request)

        return response


from django.utils.deprecation import MiddlewareMixin
from useraccount.models import GetHelpOnHomePage


class AddQuerySetToResponseMiddleware(MiddlewareMixin):
    def process_template_response(self, request, response):

        try:
            queryset = GetHelpOnHomePage.objects.filter(read_status=False).order_by(
                "-created_at"
            )
            logger.debug(queryset)
            response.context_data["get_help"] = queryset

        except Exception as e:
            logger.error("not working")
        return response
    


# _local = threading.local()

# class RequestMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         _local.request = request
#         response = self.get_response(request)
#         return response

# def get_current_request():
#     return getattr(_local, 'request', None)
