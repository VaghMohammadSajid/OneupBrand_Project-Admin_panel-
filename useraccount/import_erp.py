from django.http import JsonResponse
from oscar.core.loading import get_model
from rest_framework.decorators import api_view
import requests
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
import logging
from oscar.apps.catalogue.categories import create_from_breadcrumbs
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.utils import IntegrityError
from django.db import transaction
from django.apps import apps
from treebeard.exceptions import InvalidPosition
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
from mycustomapi.models import GSTSetup
from django.contrib import messages

Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
Partner = get_model("partner", "Partner")
StockRecord = get_model("partner", "StockRecord")
ProductClass = get_model("catalogue", "ProductClass")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")
Option = get_model("catalogue", "Option")
ProductAttribute = get_model("catalogue", "ProductAttribute")
ProductImage = get_model("catalogue", "ProductImage")


# auth_token = "token b338acdcc391620:70c91aafe0a089e"
from oneup_project.settings import ERP_URL as erp_url_setting,ERP_TOKEN

ERP_URL = (
    f"{erp_url_setting}api/method/django_ecommerce.api.get_website_items"
)
HEADERS = {
    "Authorization": f"token {ERP_TOKEN}",
    "Content-Type": "application/json",
}


@api_view(["POST"])
def bulk_product_upload(request):

    try:
        response = requests.get(ERP_URL, headers=HEADERS)
        response.raise_for_status()
        erp_data = response.json().get("message", {}).get("items", [])

        created_count = 0  # Initialize counter for created products
        processed_products = set()  # Store UPC of processed products

        with transaction.atomic():
            for product_data in erp_data:
                print(product_data, "lklk")
                item_code = product_data.get("item_code")
                if item_code in processed_products:
                    continue  # Skip if product already processed
                processed_products.add(item_code)  # Add product UPC to processed set

                item_name = product_data.get("title")
                description = product_data.get("description")
                standard_rate = product_data.get("standard_rate")
                image_url = product_data.get("image")
                item_group = product_data.get("first_category", {}).get("category")
                product_type = product_data.get("product_type")
                product_class_name = product_type if product_type else "Default"
                product_class, _ = ProductClass.objects.get_or_create(
                    name=product_class_name
                )

                parent_category_name = product_data.get("first_category", {}).get(
                    "parent_category"
                )
                parent_category = None
                if parent_category_name:
                    parent_category = Category.objects.filter(
                        name=parent_category_name
                    ).first()
                    if not parent_category:
                        parent_category = create_from_breadcrumbs(parent_category_name)

                category_name = item_group or "Default Category"
                category = Category.objects.filter(name=category_name).first()
                if not category:
                    category = create_from_breadcrumbs(item_group)

                try:
                    product = Product.objects.get(upc=item_code)
                    # Product already exists, update details if necessary
                    product.title = item_name
                    product.description = description
                    product.product_class = product_class
                    # Update other fields if needed
                    product.save()
                except Product.DoesNotExist:
                    # Product doesn't exist, create a new one
                    product = Product(
                        upc=item_code,
                        title=item_name,
                        description=description,
                        product_class=product_class,
                    )
                    product.save()
                    created_count += 1

                if image_url:
                    if not image_url.startswith(("http://", "https://")):
                        image_url = ERP_URL + image_url
                    image_response = requests.get(image_url)
                    if image_response.ok:
                        image_content = ContentFile(image_response.content)
                        product_image = ProductImage()
                        product_image.product = product
                        # Remove the '.jpg' extension from the filename
                        filename = f"{item_code}_image"  # Assuming item_code is the desired filename
                        product_image.original.save(filename, image_content, save=True)

                partner_data = product_data.get("partner", [])
                for partner_info in partner_data:
                    supplier_name = partner_info.get("supplier_name")
                    mrp = partner_info.get("mrp")
                    discount = partner_info.get("discount")
                    discount_type_erp = partner_info.get("discount_type")
                    discount_type_mapping = {
                        "percentage": "percentage",
                        "amount": "amount",
                    }
                    discount_type = discount_type_mapping.get(
                        discount_type_erp, "amount"
                    )

                    sku = partner_info.get("sku")
                    partner_instance, _ = Partner.objects.get_or_create(
                        name=supplier_name
                    )
                    partner_sku = sku if sku is not None else ""

                    gst_rate_name = partner_info.get("gst_rate")
                    gst_setup_instance = GSTSetup.objects.filter(
                        gst_rate__gst_group_code=gst_rate_name
                    ).first()

                    stock_record, created = StockRecord.objects.get_or_create(
                        product=product,
                        partner=partner_instance,
                        defaults={
                            "mrp": mrp,
                            "discount": discount,
                            "discount_type": discount_type,
                            "num_in_stock": partner_info.get("num_in_stock", 0),
                            "num_allocated": partner_info.get("num_allocated", 0),
                            "low_stock_threshold": partner_info.get(
                                "low_stock_threshold", 0
                            ),
                            "partner_sku": partner_sku,
                            "gst_rate": gst_setup_instance,
                        },
                    )
                    stock_record.save()

                variant_data = product_data.get("variant", [])
                for variant_info in variant_data:
                    attribute_name = variant_info.get("attribute_name")
                    attribute_value = variant_info.get("attribute_value")
                    attribute, _ = ProductAttribute.objects.get_or_create(
                        name=attribute_name, code=attribute_name, type="option"
                    )
                    group_name = f"{attribute_name}_options"
                    group, _ = AttributeOptionGroup.objects.get_or_create(
                        name=group_name
                    )
                    option, _ = AttributeOption.objects.get_or_create(
                        option=attribute_value, group=group
                    )

                    attribute.option_group = group
                    attribute.save()

                    if attribute not in product_class.attributes.all():
                        product_class.attributes.add(attribute)
                    try:
                        product_code = product_data.get("item_code")
                        product = Product.objects.get(upc=product_code)
                        attribute_value_instance, _ = (
                            AttributeOption.objects.get_or_create(
                                option=attribute_value, group=group
                            )
                        )
                        ProductAttributeValue.objects.update_or_create(
                            product=product,
                            attribute=attribute,
                            defaults={"value": attribute_value_instance},
                        )
                    except Product.DoesNotExist:
                        pass

                product.categories.add(category)

        response = requests.post(
            f"{ERP_URL}api/method/django_ecommerce.api.synd_data_from_django",
            json={"products": created_count},
            headers=HEADERS,
        )
        print(created_count)
        response.raise_for_status()

        return Response(
            {"message": f"{created_count} products created successfully"},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        import traceback

        traceback.print_exc(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.shortcuts import render
from .models import UploadProductJSon
from django.shortcuts import redirect
from .models import IntermediateProductTableChild

ERP_URL = (
    f"{erp_url_setting}api/method/django_ecommerce.api.get_website_items"
)
HEADERS = {
    "Authorization": f"token {ERP_TOKEN}",
    "Content-Type": "application/json",
}


def upload_page(request):

    if request.method == "POST":
        try:
            response = requests.get(ERP_URL, headers=HEADERS)
            
            logger.debug(response.__dict__)
            response.raise_for_status()

            uploaded_product = UploadProductJSon.objects.create(
                upload_json=response.json()
            )

            for single_product in response.json().get("message", {}).get("items", []):
                starting_string = ""
                for single_cate in single_product.get("first_category"):
                    inter_mediate_string = f"{single_cate} {single_product.get('first_category').get(single_cate)}"
                    starting_string = starting_string + inter_mediate_string + "\n"

                starting_string_att = ""
                for single_att in single_product.get("attributes")[0]:
                    inter_mediate_string = f"{single_att} {single_product.get('attributes')[0].get(single_att)}"
                    starting_string_att = (
                        starting_string_att + inter_mediate_string + "\n"
                    )
                IntermediateProductTableChild.objects.create(
                    json_relation=uploaded_product,
                    upc=single_product.get("item_code"),
                    title=single_product.get("title"),
                    hsn_code=single_product.get("hsn_code"),
                    description=single_product.get("description"),
                    Specification=single_product.get("Specification"),
                    image=", ".join(
                        [
                            f"{ERP_URL}" + item
                            for item in single_product.get("image")
                        ]
                    ),
                    product_type=single_product.get("product_type"),
                    is_public=single_product.get("is_public"),
                    is_discountable=single_product.get("is_discountable"),
                    best_seller=single_product.get("best_seller"),
                    standard_rate=single_product.get("standard_rate"),
                    num_in_stock=single_product.get("num_in_stock"),
                    brand=single_product.get("brand"),
                    first_category=starting_string,
                    structure=single_product.get("structure"),
                    attributes=starting_string_att,
                    recommended_products=", ".join(
                        single_product.get("recommended_products")
                    ),
                )
                for single_child in single_product.get("child_structure"):

                    starting_string = ""
                    for single_cate in single_child.get("first_category"):
                        inter_mediate_string = f"{single_cate} {single_child.get('first_category').get(single_cate)}"
                        starting_string = starting_string + inter_mediate_string + "\n"

                    starting_string_att = ""
                    for single_att in single_child.get("attributes")[0]:
                        inter_mediate_string = f"{single_att} {single_child.get('attributes')[0].get(single_att)}"
                        starting_string_att = (
                            starting_string_att + inter_mediate_string + "\n"
                        )

                    IntermediateProductTableChild.objects.create(
                        json_relation=uploaded_product,
                        upc=single_child.get("item_code"),
                        title=single_child.get("title"),
                        description=single_child.get("description"),
                        Specification=single_child.get("Specification"),
                        image=", ".join([item for item in single_product.get("image")]),
                        product_type=single_child.get("product_type"),
                        is_public=single_child.get("is_public"),
                        is_discountable=single_child.get("is_discountable"),
                        best_seller=single_child.get("best_seller"),
                        standard_rate=single_child.get("standard_rate"),
                        num_in_stock=single_child.get("num_in_stock"),
                        brand=single_child.get("brand"),
                        first_category=starting_string,
                        structure=single_child.get("structure"),
                        attributes=starting_string_att,
                        recommended_products=", ".join(
                            single_child.get("recommended_products")
                        ),
                        Parent_UPC=single_child.get("Parent_UPC"),
                        price=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("stock_record", {}).get("price")
                        ),
                        supplier=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("stock_record", {}).get("supplier")
                        ),
                        low_stock_threshold=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("stock_record", {}).get(
                                "low_stock_threshold"
                            )
                        ),
                        mrp=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("stock_record", {}).get("mrp")
                        ),
                        discount=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("stock_record", {}).get("discount")
                        ),
                        gst_rate=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("stock_record", {}).get("gst_rate")
                        ),
                        length=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("shipment_dimensions", [{}])[0].get(
                                "length"
                            )
                        ),
                        width=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("shipment_dimensions", [{}])[0].get(
                                "length"
                            )
                        ),
                        height=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("shipment_dimensions", [{}])[0].get(
                                "length"
                            )
                        ),
                        weight=(
                            None
                            if single_child.get("stock_record", {}) == None
                            else single_child.get("shipment_dimensions", [{}])[0].get(
                                "length"
                            )
                        ),
                    )
        except Exception as e:
            print(e)
            import traceback

            f = traceback.format_exc()
            logger.debug(f"error in create table{f}")
            messages.error(request, "Bulk Product Failed")
            return redirect("/useraccount/upload/")

        messages.success(
            request,
            "Bulk product upload completed. Please press the Upload Product button ",
        )

        return redirect("/useraccount/upload/")

    try:
        prod = UploadProductJSon.objects.filter().order_by("-created_date").first()
        child = IntermediateProductTableChild.objects.filter(json_relation=prod)
        return render(request, "import/import.html", {"id": prod.id, "child": child})
    except:
        return render(
            request,
            "import/import.html",
        )


def get_child_data(request, id):
    prod = UploadProductJSon.objects.get(id=id)
    child_product = IntermediateProductTableChild.objects.filter(json_relation=prod)
    return render(request, "import/child.html", {"child": child_product})


# ERP_ORDER_API
from rest_framework.response import Response
from rest_framework.views import APIView
from mycustomapi.utils.loading import get_api_classes
from apps.order.models import Order

# Assuming get_api_classes works and retrieves OrderSerializer
OrderSerializer, _, _ = get_api_classes(
    "serializers.checkout",
    ["OrderSerializer", "OrderLineSerializer", "OrderLineAttributeSerializer"],
)


class OrderListView(APIView):
    def get(self, request):
        orders = Order.objects.all()
        serialized_orders = OrderSerializer(
            orders, many=True, context={"request": request}
        ).data

        return Response(serialized_orders)


from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.http import HttpResponse


@csrf_exempt
def send_data_to_erp(request):
    url = "http://127.0.0.1:8000/useraccount/update-stock-record/"
    data = {
        "data": [
            {
                "stock_record": {
                    "supplier": "OneUp",
                    "sku": "UP101",
                    "num_in_stock": 100,
                    "num_allocated": 0,
                    "low_stock_threshold": 2,
                    "currency": "INR",
                    "mrp": 4000,
                    "discount_type": "percentage",
                    "discount": 20,
                    "gst_rate": "gst20",
                    "price": 2100,
                    "supplier_name": "OneUp",
                }
            }
        ]
    }
    # headers = {"Authorization": "token b338acdcc391620:70c91aafe0a089e"}

    try:
        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            return HttpResponse("Success Response")
        else:
            return HttpResponse(
                "Failed to send data. Status code: {}".format(response.status_code)
            )
    except Exception as e:
        return HttpResponse("An error occurred: {}".format(e))


# @csrf_exempt
# def update_stock_records(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             print("Received data:", data)
#             stock_records = data.get('data', [])
#             for record in stock_records:
#                 stock_record_data = record.get('stock_record', {})
#                 sku = stock_record_data.get('sku')
#                 if sku:
#                     discount_type_erp = stock_record_data.get('discount_type')
#                     discount_type_mapping = {
#                         'percentage': 'percentage',
#                         'amount': 'amount',
#                     }
#                     discount_type = discount_type_mapping.get(discount_type_erp, 'amount')

#                     stock_record, created = StockRecord.objects.get_or_create(
#                         partner_sku=sku,
#                         defaults={
#                             'partner_sku': stock_record_data.get('partner_sku'),
#                             'num_in_stock': stock_record_data.get('num_in_stock'),
#                             'num_allocated': stock_record_data.get('num_allocated'),
#                             'low_stock_threshold': stock_record_data.get('low_stock_threshold'),
#                             'price_currency': stock_record_data.get('currency'),
#                             'mrp': stock_record_data.get('mrp'),
#                             'discount': stock_record_data.get('discount'),
#                             'discount_type': discount_type,
#                             'gst_rate': stock_record_data.get('gst_rate'),
#                         }
#                     )
#                     if not created:
#                         stock_record.num_in_stock = stock_record_data.get('num_in_stock')
#                         stock_record.num_allocated = stock_record_data.get('num_allocated')
#                         stock_record.low_stock_threshold = stock_record_data.get('low_stock_threshold')
#                         stock_record.price_currency = stock_record_data.get('currency')
#                         stock_record.mrp = stock_record_data.get('mrp')
#                         stock_record.discount = stock_record_data.get('discount')
#                         stock_record.discount_type = discount_type
#                         gst_rate = stock_record_data.get('gst_rate')
#                         if gst_rate:
#                             gst_setup_instance, _ = GSTSetup.objects.get_or_create(gst_rate__gst_group_code=gst_rate)
#                             stock_record.gst_rate = gst_setup_instance
#                         stock_record.price = stock_record_data.get('base_price')
#                         stock_record.save()
#             print("Stock records updated successfully")
#             return JsonResponse({'message': 'Stock records updated successfully'})
#         except Exception as e:
#             print("Error:", e)
#             return JsonResponse({'error': str(e)}, status=500)

#     print("Only POST requests are allowed")
#     return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


from django.views import View
from sync_data_erp.models import StockSyncReport
from apps.order.models import StatusReprotOrderErpToAdmin


class StockIntegrations(View):
    def get(self, request):

        if request.session.get("product_upc_in_stock_report"):
            data = request.session.get("product_upc_in_stock_report")
            stock_integrations_data = StockSyncReport.objects.filter(product__upc=data)
            del request.session["product_upc_in_stock_report"]
            return render(
                request,
                "import/Stock_integraions.html",
                {"stock_integrations_data": stock_integrations_data},
            )

        elif request.session.get("product_name_in_stock_report"):

            data = request.session.get("product_name_in_stock_report")
            stock_integrations_data = StockSyncReport.objects.filter(
                product__title=data
            )
            del request.session["product_name_in_stock_report"]
            return render(
                request,
                "import/Stock_integraions.html",
                {"stock_integrations_data": stock_integrations_data},
            )
        stock_integrations_data = StockSyncReport.objects.all()
        return render(
            request,
            "import/Stock_integraions.html",
            {"stock_integrations_data": stock_integrations_data},
        )

    def post(self, request):

        if request.POST.get("upc"):
            data = request.POST.get("upc")
            request.session["product_upc_in_stock_report"] = data
        elif request.POST.get("name"):
            data = request.POST.get("name")
            request.session["product_name_in_stock_report"] = data
        return redirect("Stock-Integrations-list")


class OrderIntegrations(View):
    def get(self, request):
        order_integrations_data = StatusReprotOrderErpToAdmin.objects.all()
        return render(
            request,
            "import/Order_integrations.html",
            {"order_integrations_data": order_integrations_data},
        )


class SendJsonForProductUploadApi(APIView):

    def get(self, request):
        uploaded_product = (
            UploadProductJSon.objects.filter().order_by("-created_date").first()
        )
        return Response(
            {
                "id": uploaded_product.id,
                "upload_json": uploaded_product.upload_json,
                "erp_url": f"{ERP_URL}api/method/django_ecommerce.api.get_website_item",
                "token": f"{ERP_TOKEN}",
            }
        )
