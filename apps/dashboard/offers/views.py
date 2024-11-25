from django.shortcuts import render, redirect
from django.utils import timezone
from oscar.core.loading import get_model, get_class
import logging
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from DiscountManagement.models import ProxyClassForRange
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from oscar.apps.dashboard.offers.views import OfferListView as BaseOfferListView
from oscar.apps.dashboard.offers.views import OfferDetailView as BaseOfferDetailView
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from oscar.views import sort_queryset
from oscar.apps.dashboard.offers.forms import OfferSearchForm
from django.contrib.auth.decorators import login_required

from bannermanagement.models import RecordCreatedBy

logger = logging.getLogger(__name__)
Category = get_model("catalogue", "Category")
Product = get_model("catalogue", "Product")
Range = get_model("offer", "Range")
Condition = get_model("offer", "Condition")
Benefit = get_model("offer", "Benefit")
ConditionalOffer = get_model("offer", "ConditionalOffer")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")
AttributeOption = get_model("catalogue", "AttributeOption")
OrderDiscount = get_model("order", "OrderDiscount")
OrderDiscountCSVFormatter = get_class(
    "dashboard.offers.reports", "OrderDiscountCSVFormatter"
)
Voucher = get_model("voucher", "Voucher")


@login_required
def vouchercreateview(request, *args, **kwargs):
    if request.method == "POST":

        brand_id: list = request.POST.getlist("brands")

        selected_category = request.POST.getlist("category")

        offer_name = request.POST.get("offer_name")
        if offer_name == None:
            messages.error(request=request, message="offer name required")
            return redirect("vouchercreateview")

        description = request.POST.get("description")

        type_of_voucher = "2"
        if type_of_voucher == None:
            messages.error(request, "voucher type req")
            return redirect("vouchercreateview")
        if type_of_voucher == "1":
            type_of_offer = "Percentage"
        else:
            type_of_offer = "Fixed price"

        value_of_offer = 0

        attr_value = request.POST.getlist("attr_value")
        if len(attr_value) == None:
            messages.error(request, "attribute value required")
            return redirect("vouchercreateview")
        attr_value_query_set = AttributeOption.objects.filter(option__in=attr_value)

        if len(brand_id) > 0:
            if len(selected_category) >= 0:
                all_category = Category.objects.filter(id__in=selected_category)

                proxy_range_object = ProxyClassForRange.objects.create()
                logger.debug(attr_value_query_set)

                proxy_range_object.attr.add(*attr_value_query_set)
                logger.debug(proxy_range_object.attr.all())
                proxy_range_object.save()
                logger.debug(proxy_range_object.attr.all())

                new_range = Range.objects.create(
                    name=uuid.uuid4(),
                )
                proxy_range_object.range = new_range
                proxy_range_object.save()
                proxy_range_object.included_categories.add(*all_category)
                proxy_range_object.save()
                logger.debug(f"{proxy_range_object.included_categories.all()=}")

            else:
                proxy_range_object = ProxyClassForRange.objects.create()
                proxy_range_object.attr.add(*attr_value_query_set)
                proxy_range_object.save()
                logger.debug(f"{proxy_range_object.all_product()=}")
                new_range = Range.objects.create(
                    name=uuid.uuid4(),
                )
                proxy_range_object.range = new_range
                proxy_range_object.save()
                logger.debug(f"{proxy_range_object.__dict__=}")
        elif len(selected_category) <= 0:
            new_range = Range.objects.create(name=uuid.uuid4())
            new_range.includes_all_products = True
            new_range.save()
        else:
            new_range = Range.objects.create(name=uuid.uuid4())
            logger.debug(new_range.__dict__)
            list_of_categories = list(
                map(lambda x: Category.objects.get(id=x), selected_category)
            )
            logger.debug(list_of_categories)
            new_range.included_categories.add(*list_of_categories)
            logger.debug(new_range.all_products())

        new_condition = Condition.objects.create(range=new_range, type="Count", value=1)
        logger.debug(new_condition.__dict__)
        try:
            new_benefit = Benefit.objects.create(
                range=new_range, type=type_of_offer, value=value_of_offer
            )
        except ValidationError:
            messages.error(request=request, message="value should be number")
            return redirect("vouchercreateview")
        except:
            messages.error(request=request, message="unexpected error occured")
            return redirect("vouchercreateview")

        logger.debug(f"{new_benefit.__dict__=}")
        try:
            new_conditional_offer = ConditionalOffer.objects.create(
                name=offer_name,
                description=description,
                offer_type="Voucher",
                condition=new_condition,
                benefit=new_benefit,
                start_datetime=timezone.now(),
            )
            RecordCreatedBy.objects.create(
                created_by=request.user, conditionoffer=new_conditional_offer
            )

        except IntegrityError:
            messages.error(request=request, message="offer name already exist")
            return redirect("vouchercreateview")
        except Exception as e:
            logger.error(e)

            messages.error(request=request, message="unexpected error occured")
            return redirect("vouchercreateview")
        logger.debug(f"{new_conditional_offer.__dict__=}")
        return redirect("/dashboard/offers")

    all_category = Category.objects.all()
    all_attributes = AttributeOptionGroup.objects.all()
    
    logger.debug(f"{all_attributes[0].options.all()}")


    context = {"all_category": all_category, "all_attributes": all_attributes}
    return render(request, "oscar/dashboard/offers/step_form.html", context=context)


@login_required
def edit_offer(request, id):
    offer_instance = ConditionalOffer.objects.get(id=id)
    logger.debug(f"{offer_instance=}")

    voucher = Voucher.objects.filter(offers=offer_instance)
    logger.debug(f"{voucher=}")
    if voucher.exists():
        messages.error(
            request=request,
            message="Can't edit voucher type if voucher created with this voucher type",
        )
        return redirect("/dashboard/offers/")
    else:
        pass
    try:
        if offer_instance.benefit.range.back_range:
            logger.debug("printing inside proxy class check")
    except:
        import traceback

        traceback.print_exc()
        included_categories = (
            offer_instance.benefit.range.included_categories.all().values_list(
                "id", flat=True
            )
        )
        all_categories = Category.objects.all()
        from django.db.models import Case, When, Value, BooleanField

        queryset2 = all_categories.annotate(
            new_field=Case(
                When(id__in=included_categories, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        for i in queryset2:
            logger.debug(i.new_field)

    context = {
        "all_category": queryset2,
    }

    return render(request, "oscar/dashboard/offers/offer_edit.html", context=context)


class GetBrand(APIView):
    def post(self, request):
        data = request.data
        logger.debug(data)
        if len(data["cate"]) <= 0:
            group_data = AttributeOptionGroup.objects.filter(id__in=data["brand"])
            attr = AttributeOption.objects.filter(group__in=group_data).values_list(
                "option"
            )
            logger.debug(f"{attr=}")
            return Response({"data": attr})

        all_cate = Category.objects.filter(id__in=data.get("cate"))
        flattened_list = [
            item
            for single_cate in all_cate
            for item in single_cate.get_descendants_and_self()
        ]
        logger.debug(flattened_list)
        all_product_cate = ProductCategory.objects.filter(category__in=flattened_list)
        all_product = [
            single_product_cate.product for single_product_cate in all_product_cate
        ]
        logger.debug(all_product_cate)
        logger.debug(f"{all_product=}")
        all_product_with_child = [
            single_item
            for single_product in all_product
            for single_item in single_product.children.all()
        ]
        logger.debug(f"{all_product_with_child=}")
        logger.debug(f"{type(all_product_with_child)}")
        product_attribute = ProductAttributeValue.objects.filter(
            product__in=all_product_with_child,
            attribute__option_group__id__in=data.get("brand"),
        ).values_list("value_option__option")
        logger.debug(f"{product_attribute=}")
        # list_option_value = [option.value_option.option for option in product_attribute]
        # logger.debug(list_option_value)

        logger.debug(f"{product_attribute=}")

        logger.debug(data)
        return Response({"data": set(product_attribute)})


from itertools import chain


class GetBrandOnCate(APIView):
    def post(self, request):
        data = request.data
        logger.debug(data)
        if len(data["cate"]) <= 0:
            logger.debug(data)
            value = AttributeOptionGroup.objects.all().values_list("name", "id")
            logger.debug(f"{value}")
            return Response({"delivered": value})
        all_cate = Category.objects.filter(id__in=data.get("cate"))
        logger.debug(f"{all_cate=}")
        flattened_list = [
            item
            for single_cate in all_cate
            for item in single_cate.get_descendants_and_self()
        ]
        logger.debug(flattened_list)
        all_product_cate = ProductCategory.objects.filter(category__in=flattened_list)
        list_list_all_product = [
            single_product_cate.product.children.all()
            for single_product_cate in all_product_cate
        ]
        all_product = list(chain.from_iterable(list_list_all_product))

        product_attribute = ProductAttributeValue.objects.filter(
            product__in=all_product
        )

        print(product_attribute)

        all_attr = [
            (
                single_attr.attribute.option_group.name,
                single_attr.attribute.option_group.id,
            )
            for single_attr in product_attribute
        ]

        set_tuple = set(all_attr)
        logger.debug(all_attr)

        logger.debug(f"{set(all_attr)=}")

        return Response({"delivered": set_tuple})

    # def CalcProduct():
    #     AttributeOption.objects.filter()


class OfferListView(BaseOfferListView):
    model = ConditionalOffer
    template_name = "oscar/dashboard/offers/offer_list.html"
    context_object_name = "offers"
    form_class = OfferSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        self.search_filters = []
        qs = (
            self.model._default_manager.annotate(voucher_count=Count("vouchers"))
            .select_related("benefit", "condition")
            .order_by("-date_created")
        )
        qs = sort_queryset(
            qs,
            self.request,
            [
                "name",
                "offer_type",
                "start_datetime",
                "end_datetime",
                "num_applications",
                "total_discount",
            ],
        )

        self.form = self.form_class(self.request.GET)
        # This form is exactly the same as the other one, apart from having
        # fields with different IDs, so that they are unique within the page
        # (non-unique field IDs also break Select2)
        self.advanced_form = self.form_class(self.request.GET, auto_id="id_advanced_%s")
        if not all([self.form.is_valid(), self.advanced_form.is_valid()]):
            return qs

        name = self.form.cleaned_data["name"]
        offer_type = self.form.cleaned_data["offer_type"]
        is_active = self.form.cleaned_data["is_active"]
        has_vouchers = self.form.cleaned_data["has_vouchers"]
        voucher_code = self.form.cleaned_data["voucher_code"]

        if name:
            qs = qs.filter(name__icontains=name)
            self.search_filters.append(_('Name matches "%s"') % name)
        if is_active is not None:
            now = timezone.now()
            if is_active:
                qs = qs.filter(
                    (Q(start_datetime__lte=now) | Q(start_datetime__isnull=True))
                    & (Q(end_datetime__gte=now) | Q(end_datetime__isnull=True)),
                    status=ConditionalOffer.OPEN,
                )
                self.search_filters.append(_("Is active"))
            else:
                qs = qs.filter(Q(end_datetime__lt=now) | Q(start_datetime__gt=now))
                self.search_filters.append(_("Is inactive"))
        if offer_type:
            qs = qs.filter(offer_type=offer_type)
            self.search_filters.append(
                _('Is of type "%s"') % dict(ConditionalOffer.TYPE_CHOICES)[offer_type]
            )
        if has_vouchers is not None:
            qs = qs.filter(vouchers__isnull=not has_vouchers).distinct()
            self.search_filters.append(
                _("Has vouchers") if has_vouchers else _("Has no vouchers")
            )
        if voucher_code:
            qs = qs.filter(vouchers__code__icontains=voucher_code).distinct()
            self.search_filters.append(_('Voucher code matches "%s"') % voucher_code)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offers = []

        for offer in context["offers"]:
            offer_name = offer.name

            # Get category and attribute information
            category_info, attribute_info = "-", "-"

            try:
                range_obj = offer.condition.range.back_range
                if range_obj:
                    included_categories = (
                        range_obj.included_categories.all().values_list(
                            "name", flat=True
                        )
                    )
                    category_info = (
                        ", ".join(included_categories) if included_categories else "-"
                    )
                    included_attributes = range_obj.attr.all().values_list(
                        "option", flat=True
                    )
                    attribute_info = (
                        ", ".join(included_attributes) if included_attributes else "-"
                    )
            except Exception as e:
                range_obj = offer.condition.range
                included_categories = range_obj.included_categories.all().values_list(
                    "name", flat=True
                )
                category_info = (
                    ", ".join(included_categories) if included_categories else "-"
                )
                attribute_info = "-"
                logger.error(
                    f"Error occurred while fetching category and attribute information for offer {offer_name}: {e}"
                )

            # Get discount type from ConditionalOffer model
            discount_type = None
            if offer.benefit.type == "Percentage":
                discount_type = "Discount is a percentage off of the product's value"
            elif offer.benefit.type == "Fixed price":
                discount_type = "Discount is a fixed amount off of the product's value"

            # Get discount value from ConditionalOffer model
            discount_value = offer.benefit.value

            # Get date created from ConditionalOffer model
            date_created = offer.date_created

            # offer id
            pk = offer.pk

            # offer slug
            slug = offer.slug

            # add created by
            created_by = offer.created_users.created_by

            offers.append(
                {
                    "pk": pk,
                    "slug": slug,
                    "offer_name": offer_name,
                    "category": category_info,
                    "attribute_value": attribute_info,
                    "discount_type": discount_type,
                    "discount_value": discount_value,
                    "date_created": date_created,
                    "created_by": created_by,
                }
            )

        offers = sorted(offers, key=lambda x: x["date_created"], reverse=True)
        context["offers"] = offers
        context["form"] = self.form
        context["advanced_form"] = self.advanced_form
        context["search_filters"] = self.search_filters
        return context


class OfferDetailView(BaseOfferDetailView):
    # Slightly odd, but we treat the offer detail view as a list view so the
    # order discounts can be browsed.
    model = OrderDiscount
    template_name = "oscar/dashboard/offers/offer_detail.html"
    context_object_name = "order_discounts"
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    # pylint: disable=attribute-defined-outside-init
    def dispatch(self, request, *args, **kwargs):
        self.offer = get_object_or_404(ConditionalOffer, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if "suspend" in request.POST:
            return self.suspend()
        elif "unsuspend" in request.POST:
            return self.unsuspend()

    def suspend(self):
        if self.offer.is_suspended:
            messages.error(self.request, _("Offer is already suspended"))
        else:
            self.offer.suspend()
            messages.success(self.request, _("Offer suspended"))
        return HttpResponseRedirect(
            reverse("dashboard:offer-detail", kwargs={"pk": self.offer.pk})
        )

    def unsuspend(self):
        if not self.offer.is_suspended:
            messages.error(
                self.request,
                _("Offer cannot be reinstated as it is not currently suspended"),
            )
        else:
            self.offer.unsuspend()
            messages.success(self.request, _("Offer reinstated"))
        return HttpResponseRedirect(
            reverse("dashboard:offer-detail", kwargs={"pk": self.offer.pk})
        )

    def get_queryset(self):
        return self.model.objects.filter(offer_id=self.offer.pk).select_related("order")

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["offer"] = self.offer
        return ctx

    def render_to_response(self, context, *args, **kwargs):
        if self.request.GET.get("format") == "csv":
            formatter = OrderDiscountCSVFormatter()
            return formatter.generate_response(self.get_queryset(), offer=self.offer)
        return super().render_to_response(context, *args, **kwargs)
