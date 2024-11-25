import re
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django_tables2 import A, Column, LinkColumn, TemplateColumn

from oscar.core.loading import get_class

DashboardTable = get_class("dashboard.tables", "DashboardTable")


class UserTable(DashboardTable):
    check = TemplateColumn(
        template_name="oscar/dashboard/users/user_row_checkbox.html",
        verbose_name=" ",
        orderable=False,
    )

    email = LinkColumn("dashboard:user-detail", args=[A("id")], accessor="email")
    mobile_no = Column(accessor="username", verbose_name="Mobile No")
    name = Column(accessor="get_full_name", order_by=("last_name", "first_name"))
    active = Column(accessor="is_active")
    staff = Column(accessor="is_staff")
    date_registered = Column(accessor="date_joined")
    num_orders = Column(
        accessor="userrecord__num_orders", default=0, verbose_name=_("Number of Orders")
    )
    actions = TemplateColumn(
        template_name="oscar/dashboard/users/user_row_actions.html",
        verbose_name="Action",
        orderable=False,
    )

    icon = "fas fa-users"

    class Meta(DashboardTable.Meta):
        template_name = "oscar/dashboard/users/table.html"

    def render_mobile_no(self, value):
        """
        Render the mobile_no column, filtering out non-digit characters
        """
        digits = re.sub(r"\D", "", value)  # Extract digits from the username
        try:
            int_value = int(digits)  # Try to cast the digits to an integer
            if len(str(int_value)) == 10:  # Check if the integer has ten digits
                return int_value
            else:
                return ""
        except ValueError:
            return ""

    def render_date_registered(self, value):
        """
        Render the date_registered column with a custom date format
        """
        if value:
            return value.strftime("%d/%m/%Y %H:%M")  # Change the date format as needed
        else:
            return ""
