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
from bs4 import BeautifulSoup
import json


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

ERP_URL = (
    "http://oneuperp.stackerbee.com/api/method/django_ecommerce.api.get_website_items"
)
HEADERS = {
    "Authorization": "token b338acdcc391620:c1391947f4a80ab",
    "Content-Type": "application/json",
}


@api_view(["POST"])
def bulk_product(request):
    try:
        # Retrieve data from the ERP URL
        response = requests.get(ERP_URL, headers=HEADERS)
        response.raise_for_status()
        erp_data = response.json().get("message", {}).get("items", [])

        total_items = len(erp_data)
        items_to_create = 0
        items_not_to_create = 0
        error_details = []
        # child_error_details = []
        created_count = 0
        not_created_count = 0
        processed_products = set()
        # Analyze each product item
        for product_info in erp_data:
            structure = product_info.get("structure")
            updc = product_info.get("upc")
            try:
                product = Product.objects.get(upc=updc)
            except:
                continue
            #
            #  if :
            #     continue

            if structure == "parent":
                item_code = product_info.get("item_code")
                product_type = product_info.get("product_type")
                if not product_type:
                    error_details.append(
                        {"item_code": item_code, "reason": "Product type is missing."}
                    )
                    items_not_to_create += 1
                    continue
                if not item_code:
                    error_details.append(
                        {"item_code": item_code, "reason": "UPC is missing."}
                    )
                    items_not_to_create += 1
                    continue
                if not product_info.get("image"):
                    error_details.append(
                        {"item_code": item_code, "reason": "Image is missing."}
                    )
                    items_not_to_create += 1
                    continue
                parent_attributes = product_info.get("attributes", [])
                if not all(
                    attr.get("attribute_name") and attr.get("attribute_value")
                    for attr in parent_attributes
                ):
                    error_details.append(
                        {
                            "item_code": item_code,
                            "reason": "Attributes are missing for the parent product.",
                        }
                    )
                    items_not_to_create += 1
                    continue

                product_class, _ = ProductClass.objects.get_or_create(name=product_type)
                # Category code
                parent_category_name = product_info.get("first_category", {}).get(
                    "category"
                )
                child_category_name = product_info.get("first_category", {}).get(
                    "child_category"
                )

                parent_category = None
                if parent_category_name:
                    parent_category = Category.objects.filter(
                        name__iexact=parent_category_name
                    ).first()

                    if not parent_category and parent_category_name is not None:
                        parent_category = Category.objects.filter(
                            name__icontains=parent_category_name
                        ).first()

                    if not parent_category and parent_category_name is not None:
                        parent_category = create_from_breadcrumbs(parent_category_name)

                child_category = None
                if child_category_name:
                    if parent_category:
                        child_category = create_from_breadcrumbs(
                            f"{parent_category.name} > {child_category_name}"
                        )
                    else:
                        child_category = Category.objects.filter(
                            name__iexact=child_category_name
                        ).first()

                if not parent_category:
                    error_details.append(
                        {"item_code": item_code, "reason": "Parent category not found."}
                    )
                    items_not_to_create += 1
                    continue

                if not child_category:
                    # If child category is None, add the product to the parent category directly
                    child_category = parent_category

                if not all([parent_category, child_category]):
                    error_details.append(
                        {
                            "item_code": item_code,
                            "reason": "Parent or child category not found.",
                        }
                    )
                    items_not_to_create += 1
                    continue

                if all(
                    attr.get("attribute_name") and attr.get("attribute_value")
                    for attr in parent_attributes
                ):
                    parent_product = create_parent_product(product_info)
                    parent_product.product_class = product_class
                    parent_product.save()
                    parent_product.categories.add(child_category)
                    items_to_create += 1
                    created_count += 1

                    child_created_count = 0
                    for child_info in product_info.get("child_structure", []):
                        stock_record = child_info.get("stock_record")
                        if stock_record is None:
                            error_details.append(
                                {
                                    "item_code": child_info.get("item_code"),
                                    "reason": "Stock record is missing for a child product.",
                                }
                            )
                            items_not_to_create += 1
                            print(
                                f"Child Product Error for Item Code {child_info.get('item_code')}: Stock record is missing for a child product."
                            )
                            continue

                        # Check if attributes are missing
                        if not all(
                            attr.get("attribute_name") and attr.get("attribute_value")
                            for attr in child_info.get("attributes", [])
                        ):
                            error_details.append(
                                {
                                    "item_code": child_info.get("item_code"),
                                    "reason": "Attributes are missing for the child product.",
                                }
                            )
                            items_not_to_create += 1
                            print(
                                f"Child Product Error for Item Code {child_info.get('item_code')}: Attributes are missing for the child product."
                            )
                            continue

                        # Check if image is missing
                        if not child_info.get("image"):
                            error_details.append(
                                {
                                    "item_code": child_info.get("item_code"),
                                    "reason": "Image is missing for the child product.",
                                }
                            )
                            items_not_to_create += 1
                            print(
                                f"Child Product Error for Item Code {child_info.get('item_code')}: Image is missing for the child product."
                            )
                            continue

                        # Create child product
                        child_product = create_child_variant(parent_product, child_info)
                        child_product.product_class = parent_product.product_class
                        add_attributes_to_product(
                            child_product, child_info.get("attributes", [])
                        )
                        child_created_count += 1

        response_data = {
            "total_items": total_items,
            "items_to_create": items_to_create,
            "items_not_to_create": items_not_to_create,
            "child_created_count": child_created_count,
            "error_details": error_details,
        }
        return JsonResponse(response_data, status=201)

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to ERP URL failed: {e}")
        return JsonResponse(
            {"error": "Failed to fetch data from ERP system"}, status=500
        )

    except Exception as e:
        import traceback

        traceback.print_exc()
        logger.error(f"An unexpected error occurred: {e}")
        return JsonResponse({"error": f"An unexpected error occurred {e}"}, status=500)


def extract_specifications_from_html(html_content):
    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")
        specifications = soup.get_text(separator="\n").strip()
    else:
        specifications = ""
    return specifications


def create_parent_product(product_info):
    product_type = product_info.get("product_type")
    product_class_name = product_type if product_type else "Default"
    product_class, _ = ProductClass.objects.get_or_create(name=product_class_name)
    specifications_html = product_info.get("Specification", "")
    specifications = extract_specifications_from_html(specifications_html)

    parent_product, created = Product.objects.get_or_create(
        upc=product_info["item_code"],
        defaults={
            "title": product_info["title"],
            "description": product_info["description"],
            "specifications": specifications,
            "structure": "parent",
            "product_class": product_class,
        },
    )
    parent_product.save()
    parent_category_name = product_info.get("first_category", {}).get("parent_category")
    parent_category = None
    if parent_category_name:
        parent_category = Category.objects.filter(name=parent_category_name).first()
        if not parent_category:
            parent_category = create_from_breadcrumbs(parent_category_name)
    if parent_category:
        parent_product.categories.add(parent_category)
    if parent_product:
        add_attributes_to_product(parent_product, product_info.get("attributes", []))

    image_url = product_info.get("image")[0]
    if image_url:
        if isinstance(image_url, list):
            logger.warning(f"Unexpected type for image URL: {type(image_url)}")
            image_url = image_url[0]
        if not isinstance(image_url, str):
            logger.warning(f"Unexpected type for image URL: {type(image_url)}")
        else:
            if not image_url.startswith(("http://", "https://")):
                image_url = "http://oneuperp.stackerbee.com/" + image_url
            image_response = requests.get(image_url)
            if image_response.ok:
                image_content = ContentFile(image_response.content)
                product_image = ProductImage()
                product_image.product = parent_product
                filename = f'{product_info["item_code"]}_image'
                product_image.original.save(filename, image_content, save=True)

    return parent_product


def create_child_variant(parent_product, child_info):
    specifications_html = child_info.get("Specification", "")
    specifications = extract_specifications_from_html(specifications_html)
    child_product, created = Product.objects.get_or_create(
        upc=child_info["item_code"],
        defaults={
            "title": child_info["title"],
            "description": child_info["description"],
            "specifications": specifications,
            "structure": "child",
            "parent": parent_product,
        },
    )
    child_product.save()
    add_attributes_to_product(child_product, child_info.get("attributes", []))
    add_stock_record_to_child(child_product, child_info.get("stock_record", {}))
    image_urls = child_info.get("image")
    if image_urls:
        for image_url in image_urls:
            if not image_url.startswith(("http://", "https://")):
                image_url = "http://oneuperp.stackerbee.com/" + image_url
            image_response = requests.get(image_url)
            if image_response.ok:
                image_content = ContentFile(image_response.content)
                product_image = ProductImage()
                product_image.product = child_product
                filename = f'{child_info["item_code"]}_image'
                product_image.original.save(filename, image_content, save=True)
    return child_product


def add_attributes_to_product(product_or_class, attributes):
    print("Adding attributes to:", product_or_class)
    if product_or_class is None:
        return

    for attr in attributes:
        attribute_name = attr["attribute_name"]
        attribute_value = attr["attribute_value"]
        if attribute_value is None:
            continue
        attributes = ProductAttribute.objects.filter(
            name=attribute_name, code=attribute_name, type="option"
        )
        if attributes.exists():
            attribute = attributes.first()
        else:
            attribute = ProductAttribute.objects.create(
                name=attribute_name, code=attribute_name, type="option"
            )
        group_name = attribute_name
        groups = AttributeOptionGroup.objects.filter(name=group_name)
        if groups.exists():
            group = groups.first()
        else:
            group = AttributeOptionGroup.objects.create(name=group_name)
        option, _ = AttributeOption.objects.get_or_create(
            option=attribute_value, group=group
        )
        attribute.option_group = group
        attribute.save()
        if isinstance(product_or_class, Product):
            if product_or_class.product_class:
                try:
                    product_or_class.product_class.attributes.add(attribute)
                except:
                    pass
                """lot of issue may happen here"""
                product_attr_value, _ = ProductAttributeValue.objects.get_or_create(
                    product=product_or_class, attribute=attribute, value_option=option
                )
            else:
                print("Product class is None. Cannot add attributes.")
        elif isinstance(product_or_class, ProductClass):
            product_or_class.attributes.add(attribute)


def add_stock_record_to_child(child_product, stock_record_data):
    if stock_record_data is None:
        return
    for key, value in stock_record_data.items():
        if value is None:
            print(f"Field '{key}' has None value.")
    supplier_name = stock_record_data.get("supplier", "")
    sku = stock_record_data.get("sku", "")
    num_in_stock = stock_record_data.get("num_in_stock")
    num_allocated = stock_record_data.get("num_allocated")
    low_stock_threshold = stock_record_data.get("low_stock_threshold")
    mrp = stock_record_data.get("mrp")
    discount = stock_record_data.get("discount")
    currency = stock_record_data.get("currency", "")
    discount_type_erp = stock_record_data.get("discount_type")
    discount_type_mapping = {
        "percentage": "percentage",
        "amount": "amount",
    }
    # Convert discount_type_erp to lowercase before lookup
    discount_type_erp_lower = discount_type_erp.lower()
    discount_type = discount_type_mapping.get(discount_type_erp_lower, "amount")

    gst_rate = stock_record_data.get("gst_rate", "")
    partner_name = stock_record_data.get("partner")
    # price = stock_record_data.get('price')
    try:
        num_in_stock = float(num_in_stock) if num_in_stock is not None else 0
        num_allocated = float(num_allocated) if num_allocated is not None else 0
        low_stock_threshold = (
            float(low_stock_threshold) if low_stock_threshold is not None else 0
        )
        mrp = float(mrp) if mrp is not None else 0
        discount = float(discount) if discount is not None else 0
    except Exception as e:
        print("Exception occurred during conversion:", e)

    if None in [num_in_stock, num_allocated, low_stock_threshold, mrp, discount]:
        print("One or more numeric fields have None values after conversion.")
    else:
        print("All numeric fields have been successfully converted.")
    if discount_type not in ["amount", "percentage"]:
        discount_type = "amount"
    gst_setup_instance = None
    if not gst_rate == "" and gst_rate:
        gst_value_string_with_number = gst_rate.split()[1]
        gst_value = int(extract_numbers(gst_value_string_with_number))

        from mycustomapi.models import GSTGroup

        try:
            gst_setup_instance = GSTSetup.objects.filter(
                gst_rate__gst_group_code=gst_rate
            ).first()
        except Exception as e:
            try:
                gst_group_obj = GSTGroup.objects.get(rate=float(gst_value))
            except Exception as e:
                gst_group_obj = gst_group = GSTGroup.objects.create(
                    gst_group_code="no code",
                    rate=float(gst_value),
                )
                gst_setup_instance = GSTSetup.objects.create(
                    hsn_code=child_product.upc,
                    hsn_description="no desc",
                    gst_rate=gst_group_obj,
                )

    else:
        print("gst rate may be none ")

        child_uo = child_product.upc
        raise Exception(f"did not passed gst value for product {child_uo}")

    partner_instance = None
    if supplier_name:
        partner_instance, _ = Partner.objects.get_or_create(name=supplier_name)
    try:
        if partner_instance:
            stock_record, created = StockRecord.objects.get_or_create(
                product=child_product,
                partner=partner_instance,
                defaults={
                    "partner_sku": sku,
                    "num_in_stock": num_in_stock,
                    "num_allocated": num_allocated,
                    "low_stock_threshold": low_stock_threshold,
                    "price_currency": currency,
                    "mrp": mrp,
                    "discount": discount,
                    "discount_type": discount_type,
                    "gst_rate": gst_setup_instance,
                    # 'price': price
                },
            )
        else:
            print("Supplier name is None. Skipping stock record creation.")
    except Exception as e:
        print("Exception occurred while saving stock record:", e)


# UpDate_stockrecords_API


@csrf_exempt
def update_stock_records(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("Received data:", data)
            stock_records = data.get("data", [])
            for record in stock_records:
                stock_record_data = record.get("stock_record", {})
                sku = stock_record_data.get("sku")
                if sku:
                    discount_type_erp = stock_record_data.get("discount_type")
                    discount_type_mapping = {
                        "percentage": "percentage",
                        "amount": "amount",
                    }
                    discount_type = discount_type_mapping.get(
                        discount_type_erp, "amount"
                    )

                    stock_record, created = StockRecord.objects.get_or_create(
                        partner_sku=sku,
                        defaults={
                            "partner_sku": stock_record_data.get("partner_sku"),
                            "num_in_stock": stock_record_data.get("num_in_stock"),
                            "num_allocated": stock_record_data.get("num_allocated"),
                            "low_stock_threshold": stock_record_data.get(
                                "low_stock_threshold"
                            ),
                            "price_currency": stock_record_data.get("currency"),
                            "mrp": stock_record_data.get("mrp"),
                            "discount": stock_record_data.get("discount"),
                            "discount_type": discount_type,
                            "gst_rate": stock_record_data.get("gst_rate"),
                        },
                    )
                    if not created:
                        stock_record.num_in_stock = stock_record_data.get(
                            "num_in_stock"
                        )
                        stock_record.num_allocated = stock_record_data.get(
                            "num_allocated"
                        )
                        stock_record.low_stock_threshold = stock_record_data.get(
                            "low_stock_threshold"
                        )
                        stock_record.price_currency = stock_record_data.get("currency")
                        stock_record.mrp = stock_record_data.get("mrp")
                        stock_record.discount = stock_record_data.get("discount")
                        stock_record.discount_type = discount_type
                        gst_rate = stock_record_data.get("gst_rate")
                        if gst_rate:
                            gst_setup_instance, _ = GSTSetup.objects.get_or_create(
                                gst_rate__gst_group_code=gst_rate
                            )
                            stock_record.gst_rate = gst_setup_instance
                        stock_record.price = stock_record_data.get("base_price")
                        stock_record.save()
            print("Stock records updated successfully")
            return JsonResponse({"message": "Stock records updated successfully"})
        except Exception as e:
            print("Error:", e)
            return JsonResponse({"error": str(e)}, status=500)

    print("Only POST requests are allowed")
    return JsonResponse({"error": "Only POST requests are allowed"}, status=405)


import re


def extract_numbers(text):
    return re.sub(r"\D", "", text)
