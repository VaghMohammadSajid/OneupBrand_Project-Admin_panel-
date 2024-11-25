from django.shortcuts import render
from django.http import HttpResponse
from .forms import DiscountManagementForm
from apps.catalogue.models import Category
from apps.partner.models import StockRecord
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializer import CategorySerilaizer


def apply_discount(request):
    if request.method == "POST":
        form = DiscountManagementForm(request.POST)
        if form.is_valid():
            discount_type = form.cleaned_data["discount_type"]
            discount_amount = form.cleaned_data["discount_amount"]

            if form.cleaned_data["apply_to_all_categories"]:
                # Apply discount to all products in all categories
                apply_discount_to_all_products(discount_type, discount_amount)
            elif form.cleaned_data["selected_category"]:
                # Apply discount to all products in the selected category and its subcategories
                selected_category = form.cleaned_data["selected_category"]
                apply_discount_to_category_and_subcategories(
                    selected_category, discount_type, discount_amount
                )

            elif form.cleaned_data["selected_subcategories"]:
                # Apply discount to all products in the selected subcategories
                selected_subcategories = form.cleaned_data["selected_subcategories"]
                apply_discount_to_subcategories(
                    selected_subcategories, discount_type, discount_amount
                )

            return HttpResponse("Discount applied successfully!")

    else:
        form = DiscountManagementForm()

    return render(request, "apply_discount.html", {"form": form})


def apply_discount_to_all_products(discount_type, discount_amount):
    # Apply discount to all products in all categories
    stock_records = StockRecord.objects.all()
    for stock_record in stock_records:
        stock_record.discount_type = discount_type
        stock_record.discount = discount_amount
        stock_record.calculate_final_price()  # Calculate final price after applying the discount
        stock_record.save()


def apply_discount_to_category_and_subcategories(
    category, discount_type, discount_amount
):
    # Apply discount to all products in the selected category and its subcategories
    subcategories = list(category.get_descendants()) + [category]
    stock_records = StockRecord.objects.filter(product__categories__in=subcategories)
    for stock_record in stock_records:
        stock_record.discount_type = discount_type
        stock_record.discount = discount_amount
        stock_record.calculate_final_price()  # Calculate final price after applying the discount
        stock_record.save()


def apply_discount_to_subcategories(subcategories, discount_type, discount_amount):
    # Apply discount to all products in the selected subcategories
    stock_records = StockRecord.objects.filter(product__categories__in=subcategories)
    for stock_record in stock_records:
        stock_record.discount_type = discount_type
        stock_record.discount = discount_amount
        stock_record.calculate_final_price()  # Calculate final price after applying the discount
        stock_record.save()


class CategoryListApi(APIView):
    def get(self, request):
        all_category = Category.objects.all()
        serialized_data = CategorySerilaizer(all_category, many=True).data

        return Response({"category_list": serialized_data}, status=status.HTTP_200_OK)
