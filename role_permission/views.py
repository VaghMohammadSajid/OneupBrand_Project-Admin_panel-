from django.shortcuts import render, HttpResponse, redirect
from django.views import View
from .models import Permissions, Roles,URL_WITH_SUB
from django.contrib.auth.models import User
from django.shortcuts import redirect
import logging
from .utils import run_path_op
from .models import op_with_url_map,Role,Roles
from django.contrib import messages

logger = logging.getLogger(__name__)
PERMISSION_DICT = {
    "Catalog":{
        
        "Product":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Product Type":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Categories":{"Create":False,"Update":False,"Delete":False,"Read":False},
    },
    "Fulfilmeant":{
        "Order":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Statitics":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Customers":{"Create":False,"Update":False,"Delete":False,"Read":False},
    },
    "Voucher & Discount":{
        "Voucher Sets":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Voucher Request":{"Create":False,"Update":False,"Delete":False,"Read":False},
    },
    "Content":{
        "Main Banner":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Category Banner":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Manage Brands":{"Create":False,"Update":False,"Delete":False,"Read":False},
    },
    "Reports & Integoration":{
        "Reports":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Order Integeration":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Stock Integeration":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Product Error Log":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Product Succes Log":{"Create":False,"Update":False,"Delete":False,"Read":False},
    },
    "Wallet & Credit":{
       
        # "Credit":{"Create":False,"Update":False,"Delete":False,"Read":False},
        # "Credit Request":{"Create":False,"Update":False,"Delete":False,"Read":False},
    },
    "User":{
        "Client Requested":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Client User":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Admin User":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Get Help":{"Create":False,"Update":False,"Delete":False,"Read":False},
    },
    "Imports":{"Create":False,"Update":False,"Delete":False,"Read":False},
    "News Letter Mnanagment":{
        "Subscriber List":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Manage NewsLetter Templates":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Send News Letter":{"Create":False,"Update":False,"Delete":False,"Read":False},
        "Contact List":{"Create":False,"Update":False,"Delete":False,"Read":False},
    }

}
# Create your views here.


# def add_url(request):
#    if request.method == "POST":
#       url_str = request.POST.get("url_str")
#       Permissions.objects.create(non_permitted_url=url_str)


#       return redirect(add_url)
#    else:
#       return render(request,'role-per/add-url.html')


def add_role(request):

    if request.method == "POST":
        role_name = request.POST.get("role_name")
        
        
        temp_list = []
        if role_name is None or len(role_name) <= 0 :
            messages.error(request, "Role name Required")
            
        try:
            role_obj = Role.objects.get(role_name=role_name)
        except Role.DoesNotExist:
            role_obj = Role.objects.create(role_name=role_name)

        for i in PERMISSION_DICT:
            run_path_op(main_module=i,data=PERMISSION_DICT[i],request=request,temp_list=temp_list)

        

        for single_att in temp_list:
            
            
            if not single_att[2] in op_with_url_map[single_att[0]][single_att[1]]:
                for i in op_with_url_map[single_att[0]][single_att[1]]:
                    if isinstance(i,tuple):
                        try:
                            per_url = Permissions.objects.get(non_permitted_url=i[1])
                        except Permissions.DoesNotExist:
                            per_url = Permissions.objects.create(non_permitted_url=i[1])
                        role_obj.permission_denied.add(per_url)
        
        return redirect("add-role")
                        
                    
                    

        
        # urls = request.POST.getlist("urls")
        # # role = RoleType.objects.create(role_name=role_name)

        # print(urls)
        # for i in urls:
        #     ob = Permissions.objects.filter(non_permitted_url=i)[0]
        #     role.permissions.add(ob)
        # print(role.permissions.all())
        # return redirect(add_role)



    return render(request,'role-per/add-role.html',{"data":URL_WITH_SUB} )

# def assign_user(request):
#     print(request.user)
#     if request.method == "POST":
#         user = request.POST.get("user")
#         role_type = RoleType.objects.get(role_name=request.POST.get("role_type"))
#         user_ob = User.objects.get(username=user,)
#         Roles.objects.create(user=user_ob,role=role_type)
#     role_type = RoleType.objects.all()
#     all_user = User.objects.all()
#     return render(request,'role-per/assign-user.html',{"role_type":role_type,"all_user" :all_user})

# class AddRoleView(View):
#     template_name = 'newsletter/news_list.html'

#     def get(self, request, *args, **kwargs):

#         return render(request,'role-per/add-role.html')
#     def post(self, request, *args, **kwargs):

#         return render(request,'role-per/add-role.html')


def render_error_page(request):
    return render(request, "oscar/403.html")


def change_role(request):
    print(request.POST)
    user = request.POST.get("user")
    url_id = request.POST.getlist("on_url")
    print(user, url_id)
    user = User.objects.get(id=user)
    roles = Roles.objects.get(user=user)
    all_url = roles.role.all().values_list("id", flat=True)
    url_id_set = set(url_id)
    all_url_set = set(all_url)
    id_need_remove = all_url_set - url_id_set
    id_need_to_add = url_id_set - all_url_set
    obj_need_to_remove = Permissions.objects.filter(id__in=id_need_remove)
    obj_need_to_add = Permissions.objects.filter(id__in=id_need_to_add)
    roles.role.remove(*obj_need_to_remove)
    roles.role.add(*obj_need_to_add)

    return redirect("edit-admin", pk=user.id)


from useraccount.models import GetHelpOnHomePage
import logging

logger = logging.getLogger(__name__)


class ReadNotificationView(View):
    def post(self, request, pk):
        try:
            notification = GetHelpOnHomePage.objects.get(id=pk)
            notification.read_status = True
            notification.save()
            # Redirect to the related page; adjust according to your URL configuration
            return redirect("details-get_help", pk=pk)
        except GetHelpOnHomePage.DoesNotExist:
            logger.error(f"Notification with id {pk} does not exist.")
            return redirect("/")  # Redirect to a fallback URL or error page
        except Exception as e:
            logger.error(f"Error updating notification status: {e}")
            return redirect("/")  # Redirect to a fallback URL or error page
