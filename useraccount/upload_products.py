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
import re
from .models import UploadProductJSon
from .serializers import ParentListSerializer
from .models import UpdateErpstatus

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
    "https://oneuperp.stackerbee.com/api/method/django_ecommerce.api.update_item_status"
)
HEADERS = {
    "Authorization": "token b338acdcc391620:c1391947f4a80ab",
    "Content-Type": "application/json",
}


@api_view(["POST"])
def bulk_product(request):
    error_log = []
    child_created_count = 0
    # data = request.data.get('id')
    # response = UploadProductJSon.objects.get(id=data).upload_json

    erp_data = request.data
    total_items = 0
    items_to_create = 0
    items_created = 0
    items_not_created = 0
    child_item_skipped = 0
    parent_item_created = 0
    created_item_upc = []

    for product_info_string in erp_data:
        product_info = json.loads(product_info_string)

        structure = product_info.get("structure")

        if structure == "parent":

            total_created_list = []
            item_code = product_info.get("item_code")
            product_type = product_info.get("product_type")
            if not Product.objects.filter(upc=item_code).count() > 0:
                if not product_type:
                    error_log.append(
                        {"item_code": item_code, "reason": "Product type is missing."}
                    )
                    items_not_created += 1
                    continue
                if not item_code:
                    error_log.append(
                        {"item_code": item_code, "reason": "UPC is missing."}
                    )
                    items_not_created += 1
                    continue
                if not product_info.get("image"):
                    error_log.append(
                        {"item_code": item_code, "reason": "Image is missing."}
                    )
                    items_not_created += 1
                    continue

            parent_attributes = product_info.get("attributes", [])
            attribute_list = [i["attribute_name"] for i in parent_attributes]
            # if not all(attr.get('attribute_name') and attr.get('attribute_value') for attr in parent_attributes):
            #     error_log.append({'item_code': item_code, 'reason': 'Attributes are missing for the parent product.'})
            #     items_not_created +=1
            #     continue
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
                    if parent_category:
                        parent_category_root_or_not = parent_category.is_root()
                    else:
                        parent_category_root_or_not = False
                    if not  parent_category_root_or_not and parent_category_name is not None:
                        parent_category = create_from_breadcrumbs(parent_category_name)
            child_category = None
            if child_category_name:
                if parent_category:
                    child_category = create_from_breadcrumbs(
                        f"{parent_category.name} > {child_category_name}"
                    )
                else:
                    try:
                        child_category = Category.objects.filter(
                            name__iexact=child_category_name
                        ).first()
                    except:
                        child_category = create_from_breadcrumbs(parent_category_name)
                        parent_category = child_category

            if not parent_category:
                error_log.append(
                    {"item_code": item_code, "reason": "no category not found."}
                )
                items_not_created += 1
                continue
            if not child_category:
                # If child category is None, add the product to the parent category directly
                child_category = parent_category
            if not all([parent_category, child_category]):
                error_log.append(
                    {"item_code": item_code, "reason": "No  category not found."}
                )
                items_not_created += 1
                continue

            # if all(attr.get('attribute_name') and attr.get('attribute_value') for attr in parent_attributes):
            try:
                if Product.objects.filter(upc=item_code).count() > 0:
                    parent_product = Product.objects.filter(upc=item_code).first()
                else:
                    return_tuple = create_parent_product(product_info)
                    parent_product = return_tuple[1]
                    if not return_tuple[0]:
                        error_log.append(
                            {"item_code": parent_product.upc, "reason": parent_product}
                        )
                        parent_product.delete()

                    parent_item_created += 1

            except Exception as e:
                import traceback

                f = traceback.format_exc()
                logger.debug(f)

                error_log.append(
                    {
                        "item_code": item_code,
                        "reason": "parent product not created so skipping whole process",
                    }
                )
                continue
            parent_product.product_class = product_class
            parent_product.save()
            parent_product.categories.add(child_category)
            total_created_list.append(parent_product)
            created_item_upc.append(parent_product.upc)
            print("hwllow")
            for child_info in product_info.get("child_structure", []):
                hsn_code = product_info.get("hsn_code", {})
                if Product.objects.filter(upc=child_info.get("id")).count() > 0:
                    continue
                stock_record = child_info.get("stock_record")
                if not child_info.get("image"):
                    error_log.append(
                        {
                            "item_code": child_info.get("item_code"),
                            "reason": "Image is missing for the child product.",
                        }
                    )
                    child_item_skipped += 1
                    print(
                        f"Child Product Error for Item Code {child_info.get('item_code')}: Image is missing for the child product."
                    )
                    """need to implement code for deleting all data"""
                    continue
                if stock_record is None:
                    error_log.append(
                        {
                            "item_code": child_info.get("item_code"),
                            "reason": "Stock record is missing for a child product.",
                        }
                    )
                    child_item_skipped += 1
                    print(
                        f"Child Product Error for Item Code {child_info.get('item_code')}: Stock record is missing for a child product."
                    )
                    """need to implement code for deleting all data"""
                    continue
                if not all(
                    attr.get("attribute_name") and attr.get("attribute_value")
                    for attr in child_info.get("attributes", [])
                ):
                    error_log.append(
                        {
                            "item_code": child_info.get("item_code"),
                            "reason": "Attributes are missing for the child product.",
                        }
                    )
                    child_item_skipped += 1
                    print(
                        f"Child Product Error for Item Code {child_info.get('item_code')}: Attributes are missing for the child product."
                    )
                    """need to implement code for deleting all data"""
                    continue
                all_data = [
                    attr.get("attribute_name") for attr in child_info.get("attributes")
                ]
                if not set(all_data).issubset(attribute_list) and set(
                    attribute_list
                ).issubset(all_data):
                    error_log.append(
                        {
                            "item_code": child_info.get("item_code"),
                            "reason": "either all attributes in parent missing in child or all attributes in child missing in parent",
                        }
                    )
                    child_item_skipped += 1
                    print(
                        f"Child Product Error for Item Code {child_info.get('item_code')}: either all attributes in parent missing in child or all attributes in child missing in parent "
                    )
                    """need to implement code for deleting all data"""
                    continue

                # Create child product
                child_product = create_child_variant(
                    parent_product, child_info, hsn_code=hsn_code
                )

                if not child_product[0]:

                    error_log.append(
                        {
                            "item_code": child_info.get("item_code"),
                            "reason": child_product[1],
                        }
                    )
                    child_item_skipped += 1

                    continue
                else:
                    if child_product[1] == False:
                        print(child_product[2])

                        child_item_skipped += 1

                        error_log.append(
                            {
                                "item_code": child_info.get("item_code"),
                                "reason": child_product[2],
                            }
                        )
                        child_product[0].delete()
                        continue
                total_created_list.append(child_product[0])
                child_product[0].product_class = parent_product.product_class
                # add_attributes_to_product(child_product, child_info.get('attributes', []))
                child_created_count += 1
                created_item_upc.append(child_product[0].upc)

    from .models import IntermediateProductTableChild

    try:
        IntermediateProductTableChild.objects.filter(upc__in=created_item_upc).update(
            product_status="Item created in admin"
        )
    except:
        import traceback

        f = traceback.format_exc()
        logger.critical(f"exception occured while saving status in product table {f}")
    try:
        for upc in created_item_upc:
            UpdateErpstatus.objects.create(upc=upc)
    except Exception as e:
        import traceback

        f = traceback.format_exc()
        logger.critical(f"error in creating upc to update status {f}")

    response_data = {
        "total_items": total_items,
        "parent_item_created": parent_item_created,
        "parent_items_skipped_of_issue": items_not_created,
        "child_created_count": child_created_count,
        "child_item_skipped": child_item_skipped,
        "error_details": error_log,
    }
    logger.debug(response_data)
    return JsonResponse(response_data, status=201)


class SendStatus(APIView):
    def post(self, request):
        try:

            created_item_upc = UpdateErpstatus.objects.filter(
                update_erp=False
            ).values_list("upc", flat=True)
        except Exception as e:
            import traceback

            f = traceback.format_exc()
            logger.critical(f"error in sending data to erp for updating the status {f}")

        try:
            response = requests.post(
                url=ERP_URL, headers=HEADERS, json={"item_code": created_item_upc}
            )
            logger.debug(response.__dict__)

        except Exception as e:
            import traceback

            f = traceback.print_exc()
            logger.error(e)
            logger.error(f)

        return Response({"succes": True}, status=status.HTTP_200_OK)


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
            "is_public": product_info["is_public"],
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

        add_attributes_to_product(
            parent_product,
            product_info.get("attributes", []),
            product_info.get("product_type"),
        )
        add_brand_attrs(
            parent_product, product_info.get("brand"), product_info.get("product_type")
        )

    image_url = product_info.get("image")[0]
    for single_image in product_info.get("image"):
        image_url = single_image
        image_name = single_image.split("/")[-1]
        if image_url:
            if isinstance(image_url, list):
                logger.warning(f"Unexpected type for image URL: {type(image_url)}")
                image_url = image_url[0]
            if not isinstance(image_url, str):
                logger.warning(f"Unexpected type for image URL: {type(image_url)}")
                """need to implement code for deleting all data"""
            else:
                if not image_url.startswith(("http://", "https://")):
                    image_url = "http://oneuperp.stackerbee.com/" + image_url
                image_response = requests.get(image_url)
                if image_response.ok:
                    try:
                        image_content = ContentFile(image_response.content)
                        product_image = ProductImage()
                        product_image.product = parent_product
                        filename = image_name
                        product_image.original.save(filename, image_content, save=True)
                        try:
                            if image_name.split("-")[1][0] == "A":
                                product_image.display_order = 0
                            elif image_name.split("-")[1][0] == "B":
                                product_image.display_order = 1
                            elif image_name.split("-")[1][0] == "C":
                                product_image.display_order = 2
                            elif image_name.split("-")[1][0] == "D":
                                product_image.display_order = 3
                            elif image_name.split("-")[1][0] == "E":
                                product_image.display_order = 4
                            else:
                                product_image.display_order = 5
                        except Exception as e:
                            if str(e) == "Duplicate Image Found":
                                raise Exception("Duplicate Image Found")
                            product_image.display_order = 5

                        product_image.save()
                    except:
                        return (
                            False,
                            f"image with same name exist skipping parent item {parent_product.upc}",
                        )
    return (True, parent_product)


def create_child_variant(parent_product, child_info, hsn_code):
    specifications_html = child_info.get("Specification", "")
    specifications = extract_specifications_from_html(specifications_html)
    try:
        child_product, created = Product.objects.get_or_create(
            upc=child_info["item_code"],
            defaults={
                "title": child_info["title"],
                "description": child_info["description"],
                "specifications": specifications,
                "structure": "child",
                "parent": parent_product,
                "best_seller": True if child_info["best_seller"] else False,
                "is_public": child_info["is_public"],
            },
        )
    except:
        error = "problem with title or description specification,structer parent"
        return False, error, child_product.upc
    child_product.save()
    return_data_of_attributes = add_attributes_to_product(
        child_product,
        child_info.get("attributes", []),
        product_type=child_info.get("product_type"),
    )
    return_data_br = add_brand_attrs(
        child_product, child_info.get("brand"), child_info.get("product_type")
    )

    return_data = add_stock_record_to_child(
        child_product,
        child_info.get("stock_record", {}),
        hsncode=hsn_code,
        dimension=child_info.get("shipment_dimensions", {}),
        stock_of_child=child_info["num_in_stock"],
    )

    if not return_data_of_attributes[0]:
        return child_product, False, return_data_of_attributes[1]
    if return_data[0] == False:
        return child_product, False, return_data[1]

    image_urls = child_info.get("image")

    if image_urls:
        for image_dict in image_urls:
            logger.debug(f"{image_dict=}")
            image_url = image_dict
            image_name = image_dict.split("/")[-1]
            if not image_url.startswith(("http://", "https://")):
                image_url = "http://oneuperp.stackerbee.com/" + image_url
            image_response = requests.get(image_url)

            if image_response.ok:
                try:
                    image_content = ContentFile(image_response.content)
                    product_image = ProductImage()
                    product_image.product = child_product
                    filename = image_name
                    logger.debug(f"{filename=}")
                    product_image.original.save(filename, image_content, save=True)
                    try:
                        if image_name.split("-")[1][0] == "A":
                            product_image.display_order = 0
                        if image_name.split("-")[1][0] == "B":
                            product_image.display_order = 1
                        if image_name.split("-")[1][0] == "C":
                            product_image.display_order = 2
                        if image_name.split("-")[1][0] == "D":
                            product_image.display_order = 3
                        if image_name.split("-")[1][0] == "E":
                            product_image.display_order = 4
                    except Exception as e:
                        if str(e) == "Duplicate Image Found":
                            raise Exception("Duplicate Image Found")
                    product_image.save()
                except:
                    logger.critical(
                        f" image name with{filename} already exist skipped product with upc {child_product.upc}"
                    )
                    return (
                        child_product,
                        False,
                        f" image name with{filename} already exist skipped product with upc {child_product.upc}",
                    )

    return child_product, True, None


"""need to double check this function"""


def add_attributes_to_product(product_or_class, attributes, product_type):
    print("Adding attributes to:", product_or_class)
    if product_or_class is None:
        return
    try:
        for attr in attributes:
            print("started for loop")
            attribute_name = attr["attribute_name"]
            attribute_value = attr["attribute_value"]
            if attribute_value is None and attribute_name == "brand":
                continue
            else:
                # if attribute_value == None:
                #     attribute_value = "-"
                """all get starting from here need to be removed if we can't edit product details because our db is corrupted"""
                print("inside else")
                try:
                    attribute_group = AttributeOptionGroup.objects.get(
                        name=attribute_name
                    )
                    option_details = AttributeOption.objects.get(
                        option=attribute_value, group=attribute_group
                    )

                except AttributeOption.DoesNotExist:
                    try:
                        option_details = AttributeOption.objects.create(
                            group=attribute_group, option=attribute_value
                        )
                    except:
                        option_details = None
                except AttributeOptionGroup.DoesNotExist:
                    print(attribute_name)
                    attribute_group = AttributeOptionGroup.objects.create(
                        name=attribute_name
                    )
                    try:
                        option_details = AttributeOption.objects.get(
                            option=attribute_value, group=attribute_group
                        )
                    except:
                        try:
                            option_details = AttributeOption.objects.create(
                                group=attribute_group, option=attribute_value
                            )
                        except:

                            option_details = None

                try:
                    product_class = ProductClass.objects.get(name=product_type)
                    product_attribute = ProductAttribute.objects.get(
                        product_class=product_class, option_group=attribute_group
                    )
                except ProductClass.DoesNotExist:
                    product_class = ProductClass.objects.create(name=product_type)
                    try:
                        product_attribute = ProductAttribute.objects.get(
                            product_class=product_class,
                            option_group=attribute_group,
                            name=attribute_name,
                            type="option",
                        )
                    except ProductAttribute.DoesNotExist:
                        product_attribute = ProductAttribute.objects.create(
                            product_class=product_class,
                            option_group=attribute_group,
                            name=attribute_name,
                            type="option",
                            code=attribute_name,
                        )

                except ProductAttribute.DoesNotExist:
                    product_attribute = ProductAttribute.objects.create(
                        product_class=product_class,
                        option_group=attribute_group,
                        name=attribute_name,
                        type="option",
                        code=attribute_name,
                    )

                try:
                    product_at = ProductAttributeValue.objects.get(
                        attribute=product_attribute, product=product_or_class
                    )
                    product_at.product = product_or_class
                    print("failed")

                except:

                    product_at = ProductAttributeValue.objects.create(
                        attribute=product_attribute, product=product_or_class
                    )
                    product_at.product = product_or_class

                print("need")
                if not option_details == None:
                    product_at.value_option = option_details
                    product_at.save()

    except:
        error = "problem occured during creating attributes"

        return False, error
    return True, None


def add_stock_record_to_child(
    child_product, stock_record_data, hsncode, dimension, stock_of_child
):
    if stock_of_child == None:
        stock_of_child = 0
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
        error = "need to pass int for stock or allocated low stock or mrp or discount"
        return False, error

    if None in [num_in_stock, num_allocated, low_stock_threshold, mrp, discount]:
        print("One or more numeric fields have None values after conversion.")
    else:
        print("All numeric fields have been successfully converted.")
    if discount_type not in ["amount", "percentage"]:
        discount_type = "amount"
    gst_setup_instance = None
    if not gst_rate == "" and gst_rate:
        try:
            gst_value_string_with_number = gst_rate.split()[1]
            gst_value = int(extract_numbers(gst_value_string_with_number))
        except:
            return False, "check gst"

        from mycustomapi.models import GSTGroup

        try:
            gst_setup_instance = GSTSetup.objects.filter(
                gst_rate__gst_group_code=gst_rate
            ).first()

            if gst_setup_instance == None:
                raise GSTSetup.DoesNotExist
        except Exception as e:
            try:
                gst_group_obj = GSTGroup.objects.get(rate=float(gst_value))
            except Exception as e:
                gst_group_obj = gst_group = GSTGroup.objects.create(
                    gst_group_code=f"GST_{gst_value}",
                    rate=float(gst_value),
                )
            try:
                gst_setup_instance = GSTSetup.objects.create(
                    hsn_code=hsncode, hsn_description="no desc", gst_rate=gst_group_obj
                )
            except:

                return False, "hsn code missing"

    else:
        print("gst rate may be none ")

        child_uo = child_product.upc
        error = "no gst added"
        return False, error

    partner_instance = None
    if supplier_name:
        partner_instance, _ = Partner.objects.get_or_create(name=supplier_name)
    try:
        length = dimension[0].get("length")
        breadth = dimension[0].get("width")
        height = dimension[0].get("height")
        weight = dimension[0].get("weight")
    except:
        return False, "did not pass dimensions"
    if (
        length == None
        or length == 0
        or breadth == None
        or breadth == 0
        or height == None
        or height == 0
        or weight == None
        or weight == 0
    ):
        return False, "length or width or height or weight missing"
    try:
        if partner_instance:

            stock_record, created = StockRecord.objects.get_or_create(
                product=child_product,
                partner=partner_instance,
                defaults={
                    "partner_sku": sku,
                    "num_in_stock": stock_of_child,
                    "num_allocated": num_allocated,
                    "low_stock_threshold": low_stock_threshold,
                    "price_currency": currency,
                    "mrp": mrp,
                    "discount": discount,
                    "discount_type": discount_type,
                    "gst_rate": gst_setup_instance,
                    "breadth": breadth,
                    "weight": weight / 1000,
                    "height": height,
                    "length": length,
                    # 'price': price
                },
            )

            return stock_record, None
        else:
            logger.error("error in saving stock record",exc_info=True)
            child_uo = child_product.upc
            error = "Supplier name is None. Skipping stock record creation."

            return False, error

    except Exception as e:

        child_uo = child_product.upc
        error = "Exception occurred while saving stock record:"
        return False, error


def extract_numbers(text):
    return re.sub(r"\D", "", text)


def add_brand_attrs(product, brand, product_type):
    attribute_value = brand
    attribute_name = "brand"
    product_or_class = product
    print("brand creating")
    try:
        try:
            attribute_group = AttributeOptionGroup.objects.get(name=attribute_name)
            option_details = AttributeOption.objects.get(
                option=attribute_value, group=attribute_group
            )

        except AttributeOption.DoesNotExist:
            try:
                option_details = AttributeOption.objects.create(
                    group=attribute_group, option=attribute_value
                )
            except:

                option_details = None
        except AttributeOptionGroup.DoesNotExist:
            attribute_group = AttributeOptionGroup.objects.create(name=attribute_name)
            try:
                option_details = AttributeOption.objects.get(
                    option=attribute_value, group=attribute_group
                )
            except:
                try:
                    option_details = AttributeOption.objects.create(
                        group=attribute_group, option=attribute_value
                    )
                except:

                    option_details = None

        try:
            product_class = ProductClass.objects.get(name=product_type)
            product_attribute = ProductAttribute.objects.get(
                product_class=product_class,
                option_group=attribute_group,
                name=attribute_name,
                type="option",
            )
        except ProductClass.DoesNotExist:
            product_class = ProductClass.objects.create(name=product_type)
            try:
                product_attribute = ProductAttribute.objects.get(
                    product_class=product_class,
                    option_group=attribute_group,
                    name=attribute_name,
                    type="option",
                )
            except ProductAttribute.DoesNotExist:
                product_attribute = ProductAttribute.objects.create(
                    product_class=product_class,
                    option_group=attribute_group,
                    name=attribute_name,
                    type="option",
                )

        except ProductAttribute.DoesNotExist:
            product_attribute = ProductAttribute.objects.create(
                product_class=product_class,
                option_group=attribute_group,
                name=attribute_name,
                type="option",
            )

        try:
            product_at = ProductAttributeValue.objects.get(
                attribute=product_attribute, product=product_or_class
            )
            product_at.product = product
            print("failed")

        except:
            product_at = ProductAttributeValue.objects.create(
                attribute=product_attribute, product=product_or_class
            )
        product_at.product = product
        product_at.save()

        if not option_details == None:
            product_at.value_option = option_details
            product_at.save()
            print(type(product_at.value_option), product_at.value_option.__dict__)
            print(type(product_at), product_at.__dict__)
            print("need")
            print(option_details, product.upc)

    except:

        error = "problem occured during creating attributes"

        return False, error
    return True, None
