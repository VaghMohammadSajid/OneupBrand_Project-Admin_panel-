from oscar.apps.dashboard.catalogue import forms as base_forms
from apps.partner.models import StockRecord
from django import forms
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_class, get_classes, get_model

ProductClass = get_model("catalogue", "ProductClass")


class StockRecordForm(base_forms.StockRecordForm):
    # def __init__(self, product_class, user, *args, **kwargs):
    #     # The user kwarg is not used by stock StockRecordForm. We pass it
    #     # anyway in case one wishes to customise the partner queryset
    #     self.user = user
    #     super().__init__(*args, **kwargs)
    #     self.gst_rate = "pranav"

    class Meta(base_forms.StockRecordForm.Meta):
        model = StockRecord
        fields = [
            "partner",
            # 'partner_sku',
            "price_currency",
            "price",
            "num_in_stock",
            "low_stock_threshold",
            "discount_type",
            "discount",
            "mrp",
            "gst_rate",
            "length",
            "breadth",
            "height",
            "weight",
        ]

    def clean(self):
        cleaned_data = super().clean()

        mrp = cleaned_data.get("mrp")
        discount = cleaned_data.get("discount")
        discount_type = cleaned_data.get("discount_type")
        if mrp is not None and discount is not None:
            if discount_type == "percentage":
                cleaned_data["price"] = max(0, round(mrp - (mrp * discount / 100), 2))
            elif discount_type == "amount":
                cleaned_data["price"] = max(0, round(mrp - discount, 2))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()
        return instance


from oscar.apps.dashboard.catalogue.forms import ProductForm as BaseProductForm
from oscar.apps.dashboard.catalogue.forms import (
    ProductSearchForm as BaseProductSearchForm,
)

from django import forms
from oscar.core.loading import get_model
from oscar.forms.widgets import DateTimePickerInput

Product = get_model("catalogue", "Product")

STOCK_RECORDS_CHOICES = [
    ("---", "---"),
    ("Less than 100", "Less Than 100"),
    ("Greater than 100", "Greater Than 100"),
    ("Equal to 100", "Equal To 100"),
]


class MarginSelectWidget(forms.Select):
    def __init__(self, attrs=None):
        default_attrs = {"style": "margin-top: 15px !important;"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class ProductSearchForm(BaseProductSearchForm):
    upc = forms.CharField(max_length=64, required=False, label=_("UPC"))
    title = forms.CharField(max_length=255, required=False, label=_("Product title"))
    category = forms.CharField(max_length=255, required=False, label=_("Category"))
    sub_category = forms.CharField(
        max_length=255, required=False, label=_("Sub Category")
    )
    date_updated = forms.DateTimeField(
        required=False, label=_("Date Updated"), widget=DateTimePickerInput()
    )
    best_seller = forms.BooleanField(required=False, label=_("Best Seller"))
    featured_products = forms.BooleanField(required=False, label=_("Featured Products"))
    stock_records = forms.ChoiceField(
        required=False,
        choices=STOCK_RECORDS_CHOICES,
        label=_("Stock Records"),
        widget=MarginSelectWidget(),  # Use the custom widget here
    )

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["upc"] = cleaned_data["upc"].strip()
        cleaned_data["title"] = cleaned_data["title"].strip()
        cleaned_data["category"] = cleaned_data["category"].strip()
        cleaned_data["sub_category"] = cleaned_data["sub_category"].strip()
        cleaned_data["date_updated"] = cleaned_data.get("date_updated", None)
        cleaned_data["best_seller"] = cleaned_data.get("best_seller", False)
        cleaned_data["featured_products"] = cleaned_data.get("featured_products", False)
        cleaned_data["stock_records"] = cleaned_data.get("stock_records").strip()

        return cleaned_data


class ProductForm(BaseProductForm):
    best_seller = forms.BooleanField(required=False)
    featured_products = forms.BooleanField(required=False)
    # specifications = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Product
        fields = [
            "title",
            "upc",
            "description",
            "specifications",
            "is_public",
            "is_discountable",
            "slug",
            "meta_title",
            "meta_description",
            "best_seller",
            "featured_products",
        ]
