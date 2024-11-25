from oscar.apps.dashboard.orders.views import (
    OrderDetailView,
    OrderListView,
    sort_queryset,
)
from .models import Razorpay
from .models import Order
from homepageapi.utils import create_voucher_data
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect
from oscar.core.utils import datetime_combine, format_datetime

from useraccount.models import VocherLoginConnect
from collections import defaultdict


class OrderDetail(OrderDetailView):
    template_name = "oscar/dashboard/orders/order_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if Order.objects.get(number=self.kwargs["number"]).payment_types == "razorpay":
            raz = Razorpay.objects.get(order_id__number=self.kwargs["number"])
            ctx["raz"] = raz
        (
            total_offer_list,
            total_offer_amount,
            offer_payable,
            basic_amount_radeemable,
            total_tax,
            total_discount,
            balance_payable,
            shipping_charge,
        ) = create_voucher_data(Order.objects.get(number=self.kwargs["number"]).basket)
        print(total_offer_list)
        dict_of_code = {
            x["code"]: [x["offer"], x["voucher_gst_payable"], x["voucher_type"]]
            for x in total_offer_list
        }

        from django.db.models import F

        dict_of_vouchers = Order.objects.get(
            number=self.kwargs["number"]
        ).basket.vouchers.all()
        list_of_all_voucher_data = []
        # print(dict_of_vouchers.__dict__)

        for i in dict_of_vouchers:
            temp_dict = {}
            temp_dict["code"] = i.code
            temp_dict["name"] = i.name
            temp_dict["offer"] = dict_of_code[i.code][0]
            temp_dict["gst_payable"] = dict_of_code[i.code][1] / 2
            # temp_dict["voucher_gst_rate"] = dict_of_code[i.code][2]
            temp_dict["amount_radeemable"] = (
                temp_dict["offer"] - temp_dict["gst_payable"]
            )
            temp_dict["voucher_type"] = dict_of_code[i.code][2]
            list_of_all_voucher_data.append(temp_dict)
        print(list_of_all_voucher_data)

        ctx["total_tax"] = round(total_tax, 2)

        ctx["all_vouchers"] = list_of_all_voucher_data
        return ctx


class OrderListViewpadf(OrderListView):

    CSV_COLUMNS = {
        "date": _("Date of purchase"),
        "number": _("Order number"),
        "customer": _("Customer"),
        "num_items": _("Number of items"),
        "shipping_address_name": _("Deliver to name"),
        "value": _("Total Amount"),
        "payment_types": _("payment types"),
        "status": _("Order status"),
    }

    def get_row_values(self, order):
        row = {
            "number": order.number,
            "customer": order.user.username if order.user else "User Deleted",
            "num_items": order.num_items,
            "date": format_datetime(order.date_placed, "DATETIME_FORMAT"),
            "value": order.total_incl_tax,
            "status": order.status,
            "payment_types": order.payment_types,
        }
        if order.shipping_address:
            row["shipping_address_name"] = order.shipping_address.name
        if order.billing_address:
            row["billing_address_name"] = order.billing_address.name
        return row


class OrderListfullView(OrderListView):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        ctx["order_statuses"] = Order.all_statuses()
        ctx["search_filters"] = self.get_search_filter_descriptions()

        # Fetch all vouchers and map usernames to lists of voucher codes
        username_to_vouchers = self.get_username_to_vouchers_mapping()

        # Process orders and replace usernames with appropriate voucher codes
        orders = ctx.get("orders")
        if orders is not None:
            self.replace_usernames_with_voucher_codes(orders, username_to_vouchers)

        # Update the 'orders' in the context with the modified orders
        ctx["orders"] = orders

        return ctx

    def get(self, request, *args, **kwargs):
        if (
            "order_number" in request.GET
            and request.GET.get("response_format", "html") == "html"
        ):
            # Redirect to Order detail page if valid order number is given
            try:
                order = self.base_queryset.get(number=request.GET["order_number"])
            except Order.DoesNotExist:
                pass
            else:
                return redirect(f"/order/detail/{order.number}")
        return super().get(request, *args, **kwargs)

    def get_username_to_vouchers_mapping(self):
        vouchers = VocherLoginConnect.objects.values_list(
            "user__username", "voucher__code"
        ).order_by("-id")

        # Create a dictionary to map usernames to lists of voucher codes
        username_to_vouchers = defaultdict(list)
        for username, voucher_code in vouchers:
            username_to_vouchers[username].append(voucher_code)

        return username_to_vouchers

    def replace_usernames_with_voucher_codes(self, orders, username_to_vouchers):
        for order in orders:
            try:
                username = order.user.username
            except:
                username = None
            if username in username_to_vouchers:
                voucher_codes = username_to_vouchers[username]

                if voucher_codes:
                    chosen_voucher_code = voucher_codes.pop(0)
                    order.user.username = username
