from django.conf import settings
from django.views.generic import ListView

from oscar.core.loading import get_classes, get_model
from oscar.apps.dashboard.ranges.views import RangeListView as BaseRangeListView

Range = get_model("offer", "Range")
RangeProduct = get_model("offer", "RangeProduct")
RangeProductFileUpload = get_model("offer", "RangeProductFileUpload")
Product = get_model("catalogue", "Product")
RangeForm, RangeProductForm = get_classes(
    "dashboard.ranges.forms", ["RangeForm", "RangeProductForm"]
)


class RangeListView(BaseRangeListView):
    model = Range
    context_object_name = "ranges"
    template_name = "oscar/dashboard/ranges/range_list.html"
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        return self.model._default_manager.prefetch_related(
            "included_categories"
        ).order_by("-date_created")
