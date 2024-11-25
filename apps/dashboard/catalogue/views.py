from django.utils.translation import gettext_lazy as _

from django.db.models import Q
from django.core.paginator import Paginator
from oscar.core.loading import get_class, get_classes, get_model
from oscar.apps.dashboard.catalogue.views import ProductListView as BaseProductListView
from oscar.apps.dashboard.catalogue.views import (
    ProductClassListView as BaseProductClassListView,
)
from oscar.apps.dashboard.catalogue.views import (
    CategoryListView as BaseCategoryListView,
)

from oneup_project import settings

(
    ProductForm,
    ProductClassSelectForm,
    ProductSearchForm,
    ProductClassForm,
    CategoryForm,
    StockAlertSearchForm,
    AttributeOptionGroupForm,
    OptionForm,
) = get_classes(
    "dashboard.catalogue.forms",
    (
        "ProductForm",
        "ProductClassSelectForm",
        "ProductSearchForm",
        "ProductClassForm",
        "CategoryForm",
        "StockAlertSearchForm",
        "AttributeOptionGroupForm",
        "OptionForm",
    ),
)
(
    StockRecordFormSet,
    ProductCategoryFormSet,
    ProductImageFormSet,
    ProductRecommendationFormSet,
    ProductAttributesFormSet,
    AttributeOptionFormSet,
) = get_classes(
    "dashboard.catalogue.formsets",
    (
        "StockRecordFormSet",
        "ProductCategoryFormSet",
        "ProductImageFormSet",
        "ProductRecommendationFormSet",
        "ProductAttributesFormSet",
        "AttributeOptionFormSet",
    ),
)
ProductTable, CategoryTable, AttributeOptionGroupTable, OptionTable = get_classes(
    "dashboard.catalogue.tables",
    ("ProductTable", "CategoryTable", "AttributeOptionGroupTable", "OptionTable"),
)
(PopUpWindowCreateMixin, PopUpWindowUpdateMixin, PopUpWindowDeleteMixin) = get_classes(
    "dashboard.views",
    ("PopUpWindowCreateMixin", "PopUpWindowUpdateMixin", "PopUpWindowDeleteMixin"),
)
PartnerProductFilterMixin = get_class(
    "dashboard.catalogue.mixins", "PartnerProductFilterMixin"
)
Product = get_model("catalogue", "Product")
Category = get_model("catalogue", "Category")
ProductImage = get_model("catalogue", "ProductImage")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductClass = get_model("catalogue", "ProductClass")
StockRecord = get_model("partner", "StockRecord")
StockAlert = get_model("partner", "StockAlert")
Partner = get_model("partner", "Partner")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
Option = get_model("catalogue", "Option")


class ProductListView(BaseProductListView):
    template_name = "oscar/dashboard/catalogue/product_list.html"
    form_class = ProductSearchForm
    productclass_form_class = ProductClassSelectForm
    table_class = ProductTable  # Use ProductTable instead of DashboardTable
    context_table_name = "products"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        ctx["productclass_form"] = self.productclass_form_class()
        return ctx

    def get_description(self, form):
        if form.is_valid() and any(form.cleaned_data.values()):
            return _("Product search results")
        return _("Products")

    def get_table(self, **kwargs):
        if "recently_edited" in self.request.GET:
            kwargs.update(dict(orderable=False))

        table = super().get_table(**kwargs)
        table.caption = self.get_description(self.form)
        return table

    def get_table_pagination(self, table):
        return dict(per_page=settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE)

    def get_queryset(self):
        queryset = Product.objects.browsable_dashboard().base_queryset()
        queryset = self.filter_queryset(queryset)
        queryset = self.apply_search(queryset)
        return queryset

    def apply_search(self, queryset):
        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset
        data = self.form.cleaned_data
        upc = data.get("upc")
        if upc:
            matches_upc = Product.objects.filter(
                Q(upc__iexact=upc) | Q(children__upc__iexact=upc)
            )
            qs_match = queryset.filter(
                Q(id__in=matches_upc.values("id"))
                | Q(id__in=matches_upc.values("parent_id"))
            )
            if qs_match.exists():
                queryset = qs_match
            else:
                matches_upc = Product.objects.filter(
                    Q(upc__icontains=upc) | Q(children__upc__icontains=upc)
                )
                queryset = queryset.filter(
                    Q(id__in=matches_upc.values("id"))
                    | Q(id__in=matches_upc.values("parent_id"))
                )

        title = data.get("title")
        if title:
            queryset = queryset.filter(
                Q(title__icontains=title) | Q(children__title__icontains=title)
            )

        # Filter by Category
        category = data.get("category")
        if category:
            product_classes = ProductClass.objects.filter(name__icontains=category)
            if product_classes.exists():
                queryset = queryset.filter(product_class__in=product_classes)

        # Filter by Sub-Category
        sub_category = data.get("sub_category")
        if sub_category:
            sub_categories = Category.objects.filter(name__icontains=sub_category)
            sub_category_ids = set()
            for sub_category in sub_categories:
                # Collect IDs of sub-category and its descendants
                descendants = (
                    sub_category.get_descendants()
                )  # Make sure this is correct in your model
                sub_category_ids.update(descendants.values_list("id", flat=True))
                sub_category_ids.add(sub_category.id)  # Add the current category ID

            # Assuming 'ProductClass' has a ManyToManyField to 'Category'
            # Adjust 'product_class__categories' to the actual field in your models
            queryset = queryset.filter(categories__id__in=sub_category_ids).distinct()

        date_updated = data.get("date_updated")
        if date_updated:
            queryset = queryset.filter(
                Q(date_created__date=date_updated)
                | Q(children__date_created__date=date_updated)
                | Q(date_updated__date=date_updated)
                | Q(children__date_updated__date=date_updated)
            )

        best_seller = data.get("best_seller")
        if best_seller:
            queryset = queryset.filter(best_seller=True)

        featured_products = data.get("featured_products")
        if featured_products:
            queryset = queryset.filter(featured_products=True)

        # Search by stock_record
        stock_records = data.get("stock_records")
        if stock_records and stock_records != "---":
            if stock_records == "Less than 100":
                print("hii less than:")
                stock_records_data = StockRecord.objects.filter(num_in_stock__lte=100)
            elif stock_records == "Greater than 100":
                stock_records_data = StockRecord.objects.filter(num_in_stock__gte=101)
            elif stock_records == "Equal to 100":
                stock_records_data = StockRecord.objects.filter(num_in_stock=100)
            else:
                stock_records_data = queryset.all()

            # Filter the queryset based on the stock records
            product_ids = stock_records_data.values_list("product_id", flat=True)

            queryset = Product.objects.filter(Q(id__in=product_ids))

        return queryset.distinct()


class ProductClassListView(BaseProductClassListView):
    template_name = "oscar/dashboard/catalogue/product_class_list.html"
    context_object_name = "classes"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Product Types")

        classes = self.get_queryset()
        pagination_limit = self.request.GET.get("limit", 10)
        paginator = Paginator(classes, pagination_limit)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        ctx["classes"] = page_obj
        ctx["pagination_limit"] = int(pagination_limit)
        ctx["page_obj"] = page_obj
        ctx["page_range"] = list(paginator.page_range)

        return ctx

    def get_queryset(self):
        queryset = ProductClass.objects.all()  # Customize queryset as needed

        search_query = self.request.GET.get("name", None)
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query))

        # Apply any filters or ordering here if required
        return queryset


class CategoryListView(BaseCategoryListView):
    template_name = "oscar/dashboard/catalogue/category_list.html"
    table_class = CategoryTable
    context_table_name = "categories"

    def get_queryset(self):
        return Category.get_root_nodes()

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["child_categories"] = Category.get_root_nodes()
        return ctx
