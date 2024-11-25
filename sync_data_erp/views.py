from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Create your views here.

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import base64
import os
from oneup_project import settings
from apps.order.models import Fship_order_details, Order
from oscar.core.loading import get_model
import requests
from django.core.files.base import ContentFile
import logging
from .models import StockSyncReport
from oneup_project.settings import ERP_URL


logger = logging.getLogger(__name__)


name = {
    "items": [
        {
            "id": "OU000301-BGE-L",
            "item_code": "OU000301-BGE-L",
            "title": "LUGGAGE TROLLEY BAG-BGE-L",
            "description": "Description",
            "specification": "Specification",
            "image": [
                "/files/LUGGAGE TROLLEY BAG BEIGE L824be7.jpg",
                "/files/LUGGAGE TROLLEY BAG BEIGE L824be7.jpg",
            ],
            "product_type": "Accessories",
            "is_public": 1,
            "is_discountable": 0,
            "best_seller": 0,
            # "first_category": {
            #     "category": "ACCESSORIES",
            #     "child_category": "Luggage"
            # },
            "structure": "standalone",
            # "attributes": [
            #     {
            #         "attribute_name": "Color",
            #         "attribute_value": "Beige"
            #     },
            #     {
            #         "attribute_name": "Size",
            #         "attribute_value": "L"
            #     }
            # ],
            # "child_structure": [],
            # "recommended_products": [],
            "shipment_dimensions": [
                {"length": 50, "width": 77, "height": 31, "weight": 4600.0, "count": 1}
            ],
            # "stock_record": {
            #     "supplier": "OneUp",
            #     "num_in_stock": 0,
            #     "num_allocated": 0,
            #     "low_stock_threshold": 5,
            #     "currency": "INR",
            #     "mrp": 10999,
            #     "discount_type": "Percentage",
            #     "discount": 0,
            #     "price": 10999.0,
            #     "gst_rate": "GST 18% - OB",
            #     "supplier_name": "OneUp"
            # },
            # "price": 0
        }
    ]
}
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
ShippingEvent = get_model("order", "ShippingEvent")
ShippingEventQuantity = get_model("order", "ShippingEventQuantity")
ShippingEventType = get_model("order", "ShippingEventType")
Line = get_model("order", "Line")


class GetUPdateProduct(APIView):
    authentication_classes = []

    def post(self, request):
        sender = settings.EMAIL_HOST_USER

        try:
            logger.debug(f"update product api called {request.data.get('items')=}")
            for product_details in request.data.get("items"):
                logger.debug(f"update product api called {product_details=}")
                sender = settings.EMAIL_HOST_USER
                s = str(request.data)
                product = Product.objects.get(upc=product_details.get("id"))
                if not product.title == product_details.get("title"):
                    product.title = product_details.get("title")

                if not product.description == product_details.get("description"):
                    product.description = product_details.get("description")
                if not product.specifications == product_details.get("specification"):
                    product.specifications = product_details.get("specification")
                if not product.is_public == product_details.get("is_public"):
                    product.is_public = product_details.get("is_public")
                if not product.is_discountable == product_details.get(
                    "is_discountable"
                ):
                    product.is_discountable = product_details.get("is_discountable")
                if not product.best_seller == product_details.get("best_seller"):
                    product.best_seller = product_details.get("best_seller")
                if len(product_details.get("image")) > 0:
                    images = [
                        single_images.original for single_images in product.images.all()
                    ]
                    images_set = set(images)
                    req_image_set = set(product_details.get("image"))
                    add_set = req_image_set - images_set
                    if len(add_set) > 0:
                        delete_Set = images_set - req_image_set
                        if len(delete_Set) > 0:
                            for i in list(delete_Set):
                                ProductImage.objects.get(original=i).delete()
                        for i in list(add_set):
                            image_url = ERP_URL + i
                            image_response = requests.get(image_url)
                            image_name = i.split("/")[-1]
                            filename = image_name

                            if image_response.ok:
                                image_content = ContentFile(image_response.content)
                                product_image = ProductImage()
                                product_image.product = product
                                product_image.original.save(
                                    filename, image_content, save=True
                                )
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
                                except:
                                    product_image.display_order = 5
                                product_image.save()

                try:
                    stock = StockRecord.objects.get(product=product)
                    stock.mrp = product_details.get("stock_record").get("mrp")
                    stock.price = product_details.get("stock_record").get("price")
                    stock.save()
                except:
                    pass
                if product_details.get("shipment_dimensions"):
                    shipment_details = product_details.get("shipment_dimensions")[0]
                    stock.height = shipment_details.get("height")
                    stock.weight = shipment_details.get("weight") / 1000
                    stock.breadth = shipment_details.get("width")
                    stock.length = shipment_details.get("length")

                    stock.save()
                product.save()
                sender = settings.EMAIL_HOST_USER

        except Exception as e:
            sender = settings.EMAIL_HOST_USER
            import traceback

            traceback.print_exc()
            f = traceback.format_exc()
            logger.error(f"error in update api {f=}")
            return Response({"error": "failed"})
        return Response({"details": "success"}, status=status.HTTP_200_OK)


class GetOrderFinalDetails(APIView):
    authentication_classes = []

    def post(self, request):

        try:
            sender = settings.EMAIL_HOST_USER
            s = str(request.data)
            send_mail("order details", s, sender, ["pranavpranab@gmail.com"])
            logger.debug(f"Order api called with {s=}")
            o = Order.objects.get(number=request.data.get("order_no"))
            o.status = "To Be Shipped"
            o.save()
            product_id_list = [
                single_product_id.get("item")
                for single_product_id in request.data.get("items")
            ]
            lines_in_the_order = Line.objects.filter(
                order=o, product__upc__in=product_id_list
            )

            # obj = Fship_order_details.objects.create(order = o,sales_order_id=request.data.get("sales_order_id"),pick_up_id=request.data.get("pickup_order_id"),fship_pick_up_id=request.data.get("fship_pick_up_id"),awb_no=request.data.get("awb_no"),api_order_id=request.data.get("api_order_id"))
            try:
                shippingEventType = ShippingEventType.objects.create(
                    name="AWB Generated"
                )
            except:
                shippingEventType = ShippingEventType.objects.get(name="AWB Generated")
            logger.debug(f"{shippingEventType=}")
            new_status_change = ShippingEvent.objects.create(
                order=o, event_type=shippingEventType, notes=request.data.get("awb_no")
            )
            # new_status_change.lines.add(*lines_in_the_order)
            logger.debug(f"{lines_in_the_order=}")
            for single_line in lines_in_the_order:
                logger.debug(f"{single_line.quantity=}")
                new_event = ShippingEventQuantity.objects.create(
                    line=single_line,
                    event=new_status_change,
                    quantity=single_line.quantity,
                )
            logger.debug(f"{new_event=}")
            new_status_change.lines.add(*lines_in_the_order)

            logger.debug(f"{new_status_change}")

        except Exception as e:
            import traceback

            f = traceback.format_exc()
            logger.error(f"error in getorder final details {f=}")
            sender = settings.EMAIL_HOST_USER
            send_mail(
                "order details failed", str(e), sender, ["pranavpranab@gmail.com"]
            )

        return Response({"detail": "success"}, status=status.HTTP_200_OK)


class DeleteProductErp(APIView):
    def post(self, request):
        try:
            sender = settings.EMAIL_HOST_USER
            # send_mail("delete", str(request.data), sender, ["pranavpranab@gmail.com"])
            logger.debug(f"delete product api called with {request.data}")
        except Exception as e:
            logger.debug(f"mail not send for delete {e}")
        try:
            product_id = request.data.get("items")[0].get("id")
        except Exception as e:
            logger.error(f"product not found in delete api")
            return Response(
                {"error": "product id not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            Product.objects.get(upc=product_id).delete()
        except Product.DoesNotExist:
            logger.debug(f"product not found in delete api {product_id}")
            send_mail("delete", "not found", sender, ["pranavpranab@gmail.com"])
            return Response(
                {"error": "product not found"}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            send_mail("delete", str(e), sender, ["pranavpranab@gmail.com"])
        # send_mail("delete", str(request.data), sender, ["pranavpranab@gmail.com"])

        return Response({"data": "product deleted"}, status=status.HTTP_200_OK)


class UpdateStock(APIView):
    def post(self, request):
        try:
            sender = settings.EMAIL_HOST_USER
            # send_mail(
            #     "update stock", str(request.data), sender, ["pranavpranab@gmail.com"]
            # )
            logger.debug(f"stock update api called with {request.data}")
        except:
            try:
                logger.debug(str(request.data))
            except:
                pass
        logger.debug(f"add stock api called with data {request.data}")
        status_list = []
        try:
            for product_details in request.data.get("items"):
                try:
                    product = Product.objects.get(upc=product_details.get("id"))
                    stock = StockRecord.objects.get(product=product)
                    last_stock = stock.num_in_stock
                    stock.num_in_stock = product_details.get("num_in_stock")
                    stock.save()
                    StockSyncReport.objects.create(
                        product=product,
                        inventory=product_details.get("num_in_stock"),
                        last_stock=last_stock,
                    )

                except Exception as e:
                    logger.debug(f"{e=} inside add stock api")
                    error_dict = {
                        "upc": product_details.get("id"),
                        "status": "not created",
                    }
                    status_list.append(error_dict)
                    continue
                status_dict = {"upc": product_details.get("id"), "status": "created"}
                status_list.append(status_dict)
            return Response(
                {"succes": "ok", "status_list": status_list}, status=status.HTTP_200_OK
            )
        except Exception as e:
            import traceback

            f = traceback.format_exc()
            logger.error(f"eror in stock update api {f=}")
            return Response(
                {"error": "bad request"}, status=status.HTTP_400_BAD_REQUEST
            )


class ErpStatusApi(APIView):
    def post(self, request):
        logger.debug(f"{request.data} in erp status")
        try:
            order_id = request.data.get("order_id")
            item_upc = request.data.get("upc")
            line_status = request.data.get("status")
            order = Order.objects.get(number=order_id)
            try:
                shippingEventType = ShippingEventType.objects.get(name=line_status)
            except:
                shippingEventType = ShippingEventType.objects.create(name=line_status)
                logger.debug(f"{shippingEventType=}")
            new_status_change = ShippingEvent.objects.create(
                order=order, event_type=shippingEventType
            )
            the_lines = order.lines.all().filter(product__upc__in=item_upc)
            for single_line in the_lines:
                new_event = ShippingEventQuantity.objects.create(
                    line=single_line,
                    event=new_status_change,
                    quantity=single_line.quantity,
                )
            new_status_change.lines.add(*the_lines)
            if (
                order.lines.all().count()
                == order.shipping_events.all()
                .filter(event_type__name="To Be Shipped")
                .count()
            ):
                order.status = "To Be Shipped"
                order.save()
            elif (
                order.shipping_events.all().filter(event_type__name="To Be Shipped").count()
                > 0
            ):
                order.status = "To Be Shipped"
                order.save()
            return Response({"succes": "status changed"}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback

            f = traceback.format_exc()
            logger.critical(f"erp status issue {f=}")
            return Response(f"{f=}", status=status.HTTP_400_BAD_REQUEST)

from oscar.core.loading import get_model
Product = get_model("catalogue", "Product")
from django.http import HttpResponse
class ExcelDataErp(APIView):
    def get(self,request):
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Product Data"

        
        headers = ["Product", "UPC", "Parent UPC", "MRP", "Price",'supplier','num_stock','num_allocated','low_stock_threshold','gst_rate','hsn_code']
        ws.append(headers)

        
        for product in Product.objects.all():
            if product.structure == "child":
                product_data = [
                    str(product),  
                    product.upc,
                    product.parent.upc if product.parent else "N/A", 
                    product.stockrecords.all()[0].mrp if product.stockrecords.exists() else "N/A",
                    product.stockrecords.all()[0].price if product.stockrecords.exists() else "N/A",
                    product.stockrecords.all()[0].partner.name if product.stockrecords.exists()   else "N/A",
                    product.stockrecords.all()[0].num_in_stock if product.stockrecords.exists()   else "N/A",
                    product.stockrecords.all()[0].num_allocated if product.stockrecords.exists()   else "N/A",
                    product.stockrecords.all()[0].low_stock_threshold if product.stockrecords.exists()   else "N/A",
                    product.stockrecords.all()[0].gst_rate.gst_rate.rate if product.stockrecords.exists()   else "N/A",
                    product.stockrecords.all()[0].gst_rate.hsn_code if product.stockrecords.exists()   else "N/A",
                    
                    
                ]
                ws.append(product_data)

        
        output = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        output['Content-Disposition'] = 'attachment; filename="product_data.xlsx"'

       
        wb.save(output)
        return output
