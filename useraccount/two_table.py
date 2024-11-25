import logging
from .models import (
    IntermediateProductTableChild,
    IntermediateProductTableSucces,
    IntermediateProductTableError,
    UploadProductJSon,
    ProductUploadSuccesLog,
    ProductUploadErrorLog,
)

from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class CreateTwoTablesApi(APIView):
    def post(self, request):
        upload_id = request.data.get("id")
        error_list = request.data.get("error_list")
        succes_list = request.data.get("succes_list")
        logger.debug(upload_id)
        logger.debug(error_list)
        logger.debug(succes_list)
        json_ob = UploadProductJSon.objects.get(id=upload_id)
        if succes_list is not None:
            succes_product_data = IntermediateProductTableChild.objects.filter(
                json_relation=json_ob, upc__in=succes_list
            )
            success_log = ProductUploadSuccesLog.objects.create()
            instances_to_create = [
                IntermediateProductTableSucces(
                    log_date_conn=success_log,
                    gst_rate=product.gst_rate,
                    price=product.price,
                    discount=product.discount,
                    mrp=product.mrp,
                    low_stock_threshold=product.low_stock_threshold,
                    supplier=product.supplier,
                    weight=product.weight,
                    height=product.height,
                    width=product.width,
                    length=product.length,
                    recommended_products=product.recommended_products,
                    structure=product.structure,
                    Parent_UPC=product.Parent_UPC,
                    attributes=product.attributes,
                    first_category=product.first_category,
                    brand=product.brand,
                    num_in_stock=product.num_in_stock,
                    standard_rate=product.standard_rate,
                    best_seller=product.best_seller,
                    is_discountable=product.is_discountable,
                    is_public=product.is_public,
                    product_type=product.product_type,
                    image=product.image,
                    Specification=product.Specification,
                    description=product.description,
                    title=product.title,
                    hsn_code=product.hsn_code,
                    upc=product.upc,
                )
                for product in succes_product_data
            ]

            total_length = len(instances_to_create)
            success_log.upload_count = total_length
            success_log.save()
            IntermediateProductTableSucces.objects.bulk_create(instances_to_create)
        if error_list is not None:
            error_log_obj = ProductUploadErrorLog.objects.create()
            i = 0
            for single_error_data in error_list:
                i = i + 1
                error = single_error_data["reason"]
                upc = single_error_data["id"]
                logger.debug(upc)
                product = IntermediateProductTableChild.objects.get(
                    json_relation=json_ob, upc=upc
                )
                IntermediateProductTableError.objects.create(
                    log_date_conn=error_log_obj,
                    gst_rate=product.gst_rate,
                    price=product.price,
                    discount=product.discount,
                    mrp=product.mrp,
                    low_stock_threshold=product.low_stock_threshold,
                    supplier=product.supplier,
                    weight=product.weight,
                    height=product.height,
                    width=product.width,
                    length=product.length,
                    recommended_products=product.recommended_products,
                    structure=product.structure,
                    Parent_UPC=product.Parent_UPC,
                    attributes=product.attributes,
                    first_category=product.first_category,
                    brand=product.brand,
                    num_in_stock=product.num_in_stock,
                    standard_rate=product.standard_rate,
                    best_seller=product.best_seller,
                    is_discountable=product.is_discountable,
                    is_public=product.is_public,
                    product_type=product.product_type,
                    image=product.image,
                    Specification=product.Specification,
                    description=product.description,
                    title=product.title,
                    hsn_code=product.hsn_code,
                    error=error,
                )
            error_log_obj.upload_count = i
            error_log_obj.save()
        IntermediateProductTableChild.objects.filter(json_relation=json_ob).delete()
        return Response({"succes": True})
