from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django_tables2 import A, Column, LinkColumn, TemplateColumn

from oscar.apps.dashboard.catalogue.tables import ProductTable as BaseProductTable

from oscar.core.loading import get_class, get_model

DashboardTable = get_class("dashboard.tables", "DashboardTable")
Product = get_model("catalogue", "Product")


class ProductTable(BaseProductTable):

    title = TemplateColumn(
        verbose_name=_("Title"),
        template_name="oscar/dashboard/catalogue/product_row_title.html",
        order_by="title",
        accessor=A("title"),
    )
    image = TemplateColumn(
        verbose_name=_("Image"),
        template_name="oscar/dashboard/catalogue/product_row_image.html",
        orderable=False,
    )
    product_class = Column(
        verbose_name=_("Product Type"),
        accessor=A("product_class"),
        order_by="product_class__name",
    )
    variants = TemplateColumn(
        verbose_name=_("Variants"),
        template_name="oscar/dashboard/catalogue/product_row_variants.html",
        orderable=False,
    )
    stock_records = TemplateColumn(
        verbose_name=_("Stock Records"),
        template_name="oscar/dashboard/catalogue/product_row_stockrecords.html",
        orderable=False,
    )
    actions = TemplateColumn(
        verbose_name=_("Actions"),
        template_name="oscar/dashboard/catalogue/product_row_actions.html",
        orderable=False,
    )
    date_updated = TemplateColumn(
        verbose_name=_("Date Updated"),
        template_name="oscar/dashboard/catalogue/product_row_date_updated.html",
        orderable=True,
    )

    icon = "fas fa-sitemap"

    class Meta(DashboardTable.Meta):
        model = Product
        fields = (
            "upc",
            "is_public",
            "best_seller",
            "featured_products",
            "date_updated",
        )
        sequence = (
            "title",
            "upc",
            "image",
            "product_class",
            "variants",
            "stock_records",
            "...",
            "is_public",
            "best_seller",
            "featured_products",
            "date_updated",
            "actions",
        )
        order_by = "-date_updated"
