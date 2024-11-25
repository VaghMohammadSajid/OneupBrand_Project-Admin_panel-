from django.db import models
from django.contrib.auth.models import User


# Create your models here.
all_url_dict = {
    "product_list": "get/dashboard/catalogue/",
    "product_detail_view": "get/dashboard/catalogue/products//",
    "product_update_view": "post/dashboard/catalogue/products//",
    "product_create_view": "get/dashboard/catalogue/products/create/",
    "list_product_type": "get/dashboard/catalogue/product-types/",
    "product_type_detail": "get/dashboard/catalogue/product-type//update/",
    "product_type_update": "post/dashboard/catalogue/product-type//update/",
    "delete_product_type": "post/dashboard/catalogue/product-type//delete/",
    "add_product_type": "get/dashboard/catalogue/product-type/create/",
    "add_categories": "get/dashboard/catalogue/categories/create/",
    "list_categories": "get/dashboard/catalogue/categories/",
    "view_categories": "get/dashboard/catalogue/categories//update/",
    "update_categories": "post/dashboard/catalogue/categories//update/",
    "add_child": "get/dashboard/catalogue/categories/create//",
    "delete_categories": "get/dashboard/catalogue/categories//delete/",
    "order_list": "get/order/full-orders",
    "order-detail": "get/order/detail//",
    "order_edit": "post/order/detail//",
    "order_statics": "get/dashboard/orders/statistics/",
    "customers": "get/dashboard/users/",
    "voucher_type": "get/dashboard/offers/",
    "add_voucher": "get/voucher_type/add_vaoucher_type/",
    "delete_voucher_type": "get/dashboard/offers//",
    "list_vouchers": "get/bannermanage/voucher-sets/",
    "voucher_detail": "/get/dashboard/vouchers/sets/detail//",
    "voucher_request": "get/bannermanage/voucher-request-user-list/",
    "banner_list": "get/bannermanage/banner-list/",
    "add_banners": "get/bannermanage/add-banner/",
    "edit_banner": "get/bannermanage/edit-banner//",
    "category_banner": "get/bannermanage/CategoryPromotionList-list/",
    "add_category": "get/bannermanage/add-categorypromotion/",
    "list_brand": "get/bannermanage/manage_brands_list/",
    "add_brand": "get/bannermanage/manage_brands/",
    "reports": "get/dashboard/reports/",
    "order_integeration": "get/useraccount/Order-Integrations-list/",
    "stock_integeration": "get/useraccount/Stock-Integrations-list/",
    "wallet_list": "get/wallet/total_amount/",
    "product_upload": "get/useraccount/upload/",
    "subscribers_list": "get/MyNewsLetterApi/subscriber-list/",
    "news_letter_template": "get/MyNewsLetterApi/Manage-NewsLetter-Template/",
    "send_news_letter": "get/MyNewsLetterApi/send-newsletter/",
    "contact_list": "get/useraccount/contact-list/",
}


URL_WITH_SUB = {
    "Catalog":{
        
        "Product":["Create","Update","Delete","Read"],
        "Product Type":["Create","Update","Delete","Read"],
        "Categories":["Create","Update","Delete","Read"],
    },
    "Fulfilmeant":{
        "Order":["Create","Update","Delete","Read"],
        "Statitics":["Create","Update","Delete","Read"],
        "Customers":["Create","Update","Delete","Read"],
    },
    "Voucher & Discount":{
       
        "Voucher Sets":["Create","Update","Delete","Read"],
        "Voucher Request":["Create","Update","Delete","Read"],
    },
    "Content":{
        "Main Banner":["Create","Update","Delete","Read"],
        "Category Banner":["Create","Update","Delete","Read"],
        "Manage Brands":["Create","Update","Delete","Read"],
    },
    "Reports & Integoration":{
        "Reports":["Create","Update","Delete","Read"],
        "Order Integeration":["Create","Update","Delete","Read"],
        "Stock Integeration":["Create","Update","Delete","Read"],
        "Product Error Log":["Create","Update","Delete","Read"],
        "Product Succes Log":["Create","Update","Delete","Read"],
    },
    "Wallet & Credit":{
        
        "Credit":["Create","Update","Delete","Read"],
        "Credit Request":["Create","Update","Delete","Read"],
    },
    "User":{
        "Client Requested":["Create","Update","Delete","Read"],
        "Client User":["Create","Update","Delete","Read"],
        "Admin User":["Create","Update","Delete","Read"],
        "Get Help":["Create","Update","Delete","Read"],   
    },
    "Imports":["Create","Update","Delete","Read"],
    "News Letter Mnanagment":{
        "Subscriber List":["Create","Update","Delete","Read"],
        "Manage NewsLetter Templates":["Create","Update","Delete","Read"],
        "Send News Letter":["Create","Update","Delete","Read"],
        "Contact List":["Create","Update","Delete","Read"],
    }

}

class Permissions(models.Model):
    url_name = models.TextField(blank=True, null=True)
    non_permitted_url = models.CharField(max_length=200, unique=True,db_index=True)

    def __str__(self):
        return f"{self.non_permitted_url}"
    
class Role(models.Model):
    role_name = models.TextField(blank=True,null=True,db_index=True)
    permission_denied = models.ManyToManyField(Permissions)

    def __str__(self):
        return f'{self.role_name}'


class Roles(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role,on_delete=models.CASCADE,blank=True,null=True)

    def __str__(self):
        return self.user.username


def create_url():
    for i in all_url_dict:
        single_url = all_url_dict[i]
        url = single_url.split("/")
        url.pop(0)
        print(url)
        url = "/".join(url)
        print(url)
        try:
            Permissions.objects.create(non_permitted_url=url, url_name=i)
        except:
            pass



"""
need to implement product delete view
order create delete
customer create edit and delete,
voucher delete and update and need to include detail
delete_banner
category banner delete and update
update and delete brands
report create delete and update
stock integeration create update and delete
order integeration update delete and create
product error log and product success log all
credit and credit req all



"""

op_with_url_map = {
    "Catalog":{
        
        "Product":[("Create",all_url_dict["product_create_view"]), ("Update",all_url_dict["product_update_view"]),("Delete",all_url_dict["product_create_view"]), ("Read",all_url_dict["product_list"])],
        "Product Type":[("Create",all_url_dict["add_product_type"]),("Update",all_url_dict["product_type_update"]),("Delete",all_url_dict["delete_product_type"]),("Read",all_url_dict["list_product_type"])],
        "Categories":[("Create",all_url_dict["add_categories"]),("Update",all_url_dict["update_categories"]),("Delete",all_url_dict["delete_product_type"]),("Read",all_url_dict["list_categories"])],
    },
    "Fulfilmeant":{
        "Order":[("Create",all_url_dict["product_create_view"]),("Update",all_url_dict["order_edit"]),("Delete",all_url_dict["product_create_view"]),("Read",all_url_dict["order_list"])],
        "Statitics":["Create","Update","Delete",("Read",all_url_dict["order_statics"])],
        "Customers":[("Create"),("Update"),("Delete"),("Read",all_url_dict["customers"])],
    },
    "Voucher & Discount":{
        # "Voucher Type":["Create","Update","Delete","Read"],
        "Voucher Sets":[("Create",all_url_dict["add_voucher"]),("Update",all_url_dict["product_create_view"]),("Delete",all_url_dict["product_create_view"]),("Read",all_url_dict["list_vouchers"])],
        "Voucher Request":["Create","Update","Delete",("Read",all_url_dict["voucher_request"])],
    },
    "Content":{
        "Main Banner":[("Create",all_url_dict["add_banners"]),("Update",all_url_dict["edit_banner"]),("Delete",all_url_dict["add_voucher"]),("Read",all_url_dict["banner_list"])],
        "Category Banner":[("Create",all_url_dict["add_category"]),"Update","Delete",("Read",all_url_dict["category_banner"])],
        "Manage Brands":[("Create",all_url_dict["add_brand"]),"Update","Delete",("Read",all_url_dict["list_brand"])],
    },
    "Reports & Integoration":{
        "Reports":["Create","Update","Delete",("Read",all_url_dict["reports"])],
        "Order Integeration":["Create","Update","Delete",("Read",all_url_dict["order_integeration"])],
        "Stock Integeration":["Create","Update","Delete",("Read",all_url_dict["stock_integeration"])],
        "Product Error Log":["Create","Update","Delete","Read"],
        "Product Succes Log":["Create","Update","Delete","Read"],
    },
    "Wallet & Credit":{
        # "Wallet":["Create","Update","Delete","Read"],
        # "Credit":["Create","Update","Delete",("Read",all_url_dict["contact_list"])],
        "Credit Request":["Create","Update","Delete","Read"],
    },
    "User":{
        "Client Requested":["Create","Update","Delete","Read"],
        "Client User":["Create","Update","Delete","Read"],
        "Admin User":["Create","Update","Delete","Read"],
        "Get Help":["Create","Update","Delete","Read"],   
    },
    "Imports":["Create","Update","Delete",("Read",all_url_dict["product_upload"])],
    "News Letter Mnanagment":{
        "Subscriber List":["Create","Update","Delete",("Read",all_url_dict['subscribers_list'])],
        "Manage NewsLetter Templates":["Create","Update","Delete",("Read",all_url_dict["news_letter_template"])],
        "Send News Letter":["Create","Update","Delete",("Read",all_url_dict['send_news_letter'])],
        "Contact List":["Create","Update","Delete",("Read",all_url_dict["contact_list"])],
    }

}
