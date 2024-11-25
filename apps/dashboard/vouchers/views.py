from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import DetailView
from oscar.apps.dashboard.vouchers.views import VoucherSetDownloadView
from oscar.core.utils import slugify

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import generic, View

from oscar.core.loading import get_class, get_model
from oscar.core.utils import slugify
from oscar.views import sort_queryset
import logging

logger = logging.getLogger(__name__)
from bannermanagement.models import VoucherSet

VoucherForm = get_class("dashboard.vouchers.forms", "VoucherForm")
VoucherSetForm = get_class("dashboard.vouchers.forms", "VoucherSetForm")
VoucherSetSearchForm = get_class("dashboard.vouchers.forms", "VoucherSetSearchForm")
VoucherSearchForm = get_class("dashboard.vouchers.forms", "VoucherSearchForm")
Voucher = get_model("voucher", "Voucher")
VoucherSets = get_model("voucher", "VoucherSet")
OrderDiscount = get_model("order", "OrderDiscount")


class VoucherListView(generic.ListView):
    model = Voucher
    context_object_name = "vouchers"
    template_name = "oscar/dashboard/vouchers/voucher_list.html"
    form_class = VoucherSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        self.search_filters = []
        qs = self.model._default_manager.all()
        qs = qs.annotate(num_offers=Count("offers", distinct=True))
        qs = sort_queryset(
            qs,
            self.request,
            ["num_basket_additions", "num_orders", "num_offers", "date_created"],
            "-date_created",
        )

        # If form is not submitted, perform a default filter, and return early
        if not self.request.GET:
            self.form = self.form_class(initial={"in_set": False})
            # This form is exactly the same as the other one, apart from having
            # fields with different IDs, so that they are unique within the page
            # (non-unique field IDs also break Select2)
            self.advanced_form = self.form_class(
                initial={"in_set": False}, auto_id="id_advanced_%s"
            )
            self.search_filters.append(_("Not in a set"))
            return qs.filter(voucher_set__isnull=True)

        self.form = self.form_class(self.request.GET)
        # This form is exactly the same as the other one, apart from having
        # fields with different IDs, so that they are unique within the page
        # (non-unique field IDs also break Select2)
        self.advanced_form = self.form_class(self.request.GET, auto_id="id_advanced_%s")
        if not all([self.form.is_valid(), self.advanced_form.is_valid()]):
            return qs

        name = self.form.cleaned_data["name"]
        code = self.form.cleaned_data["code"]
        offer_name = self.form.cleaned_data["offer_name"]
        is_active = self.form.cleaned_data["is_active"]
        in_set = self.form.cleaned_data["in_set"]
        has_offers = self.form.cleaned_data["has_offers"]

        if name:
            qs = qs.filter(name__icontains=name)
            self.search_filters.append(_('Name matches "%s"') % name)
        if code:
            qs = qs.filter(code=code)
            self.search_filters.append(_('Code is "%s"') % code)
        if offer_name:
            qs = qs.filter(offers__name__icontains=offer_name)
            self.search_filters.append(_('Offer name matches "%s"') % offer_name)
        if is_active is not None:
            now = timezone.now()
            if is_active:
                qs = qs.filter(start_datetime__lte=now, end_datetime__gte=now)
                self.search_filters.append(_("Is active"))
            else:
                qs = qs.filter(end_datetime__lt=now)
                self.search_filters.append(_("Is inactive"))
        if in_set is not None:
            qs = qs.filter(voucher_set__isnull=not in_set)
            self.search_filters.append(_("In a set") if in_set else _("Not in a set"))
        if has_offers is not None:
            qs = qs.filter(offers__isnull=not has_offers).distinct()
            self.search_filters.append(
                _("Has offers") if has_offers else _("Has no offers")
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        ctx["advanced_form"] = self.advanced_form
        ctx["search_filters"] = self.search_filters
        return ctx


class VoucherSetCreateView(generic.CreateView):
    model = VoucherSets
    template_name = "oscar/dashboard/vouchers/voucher_set_form.html"
    form_class = VoucherSetForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Create voucher set")
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        initial["start_datetime"] = timezone.now()
        return initial

    def get_success_url(self):
        messages.success(self.request, _("Voucher set created"))
        return reverse("add-voucher")


from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter


class VoucherSetUpdateView(generic.UpdateView):
    template_name = "oscar/dashboard/vouchers/voucher_set_form.html"
    model = VoucherSets
    context_object_name = "voucher_set"
    form_class = VoucherSetForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.object.name
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        # All vouchers in the set have the same "usage" and "offers", so we use
        # the first one
        voucher = self.object.vouchers.first()
        if voucher is not None:
            initial["usage"] = voucher.usage
            initial["offers"] = voucher.offers.all()
        return initial

    def get_success_url(self):
        try:
            voucher_id = self.object.pk
            print("voucher:", voucher_id)
            voucher_sets = VoucherSet.objects.filter(voucher__id=voucher_id)
            if voucher_sets.exists():
                # Assuming you want to redirect to the first found voucher set
                first_voucher_set = voucher_sets.first()
                print("voucher_sets:", first_voucher_set.id)
                messages.success(self.request, _("Voucher Updated"))
                return reverse(
                    "edit-voucherset", kwargs={"voucher_id": first_voucher_set.id}
                )
            else:
                # Handle the case when no voucher sets are found
                messages.error(self.request, _("No Vouchers Found"))
                return reverse(
                    "voucher-sets"
                )  # Replace with the URL you want to redirect to
        except ObjectDoesNotExist:
            # Handle the case when voucher object does not exist
            messages.error(self.request, _("Voucher not found"))
            return reverse(
                "voucher-sets"
            )  # Replace with the URL you want to redirect to


class VoucherSetDetailView(generic.ListView):
    model = Voucher
    context_object_name = "vouchers"
    template_name = "oscar/dashboard/vouchers/voucher_set_detail.html"
    form_class = VoucherSetSearchForm
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):

        self.voucher_set = get_object_or_404(VoucherSets, pk=kwargs["pk"])
        voucher_set = VoucherSet.objects.filter(voucher__id=self.voucher_set.id)
        vouchers = Voucher.objects.filter(voucher_set_id=self.voucher_set.id).values()
        for i in vouchers:
            # print(i["code"])
            masked_string = i["code"][:5] + "*" * 4 + i["code"][9:14]
            i["code"] = masked_string

        if voucher_set.exists():
            voucher_set = voucher_set.all().first()
            print(voucher_set)
            return render(
                request,
                self.template_name,
                {"voucher_set": voucher_set, "vouchers": vouchers},
            )
        else:
            messages.error(self.request, _("voucher_set not found"))
            return reverse("voucher-sets")

    def get_queryset(self):

        self.search_filters = []
        qs = self.model.objects.filter(voucher_set=self.voucher_set).order_by(
            "-date_created"
        )

        qs = sort_queryset(
            qs,
            self.request,
            ["num_basket_additions", "num_orders", "date_created"],
            "-date_created",
        )

        # If form not submitted, return early
        is_form_submitted = "name" in self.request.GET or "code" in self.request.GET
        if not is_form_submitted:
            self.form = self.form_class()
            return qs

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return qs

        data = self.form.cleaned_data
        if data["code"]:
            qs = qs.filter(code__icontains=data["code"])
            self.search_filters.append(_('Code matches "%s"') % data["code"])

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        print("VoucherSetDetailView")
        ctx["voucher_set"] = self.voucher_set
        print(self.voucher_set)
        ctx["form"] = self.form
        ctx["search_filters"] = self.search_filters
        return ctx


class VoucherSetDeleteView(generic.DeleteView):
    model = VoucherSets
    template_name = "oscar/dashboard/vouchers/voucher_set_delete.html"
    context_object_name = "voucher_set"

    def get(self, request, *args, **kwargs):
        self.voucher_set = get_object_or_404(VoucherSets, pk=kwargs["pk"])
        voucher_set = VoucherSet.objects.filter(voucher__id=self.voucher_set.id)
        vouchers = Voucher.objects.filter(voucher_set_id=self.voucher_set.id)
        if voucher_set.exists():
            voucher_set = voucher_set.all().first()
            return render(request, self.template_name, {"voucher_set": voucher_set})

    def get_success_url(self):
        try:
            voucher_id = self.object.pk
            voucher_sets = VoucherSet.objects.filter(voucher__id=voucher_id)
            if voucher_sets.exists():
                # Assuming you want to redirect to the first found voucher set
                first_voucher_set = voucher_sets.first()
                first_voucher_set.delete()

                messages.success(self.request, _("Voucher set deleted"))
                return reverse("voucher-sets")
            else:
                # Handle the case when no voucher sets are found
                messages.error(self.request, _("No Vouchers Found"))
                return reverse(
                    "voucher-sets"
                )  # Replace with the URL you want to redirect to
        except ObjectDoesNotExist:
            # Handle the case when voucher object does not exist
            messages.error(self.request, _("Voucher not found"))
            return reverse(
                "voucher-sets"
            )  # Replace with the URL you want to redirect to


from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from django.db.models import F, Func, ExpressionWrapper, Value, CharField
from oscar.apps.voucher.models import Voucher
from django.db.models import Func, F
from django.core.mail import EmailMessage
from bannermanagement.models import VoucherSet as Vou


def date_formatter(vale):
    return ExpressionWrapper(
        Func(F(vale), Value("DD/MM/YYYY"), function="to_char"), output_field=CharField()
    )


def generate_pdf(voucher_set):
    voucher = (
        Voucher.objects.filter(voucher_set=voucher_set)
        .annotate(
            end_dates=date_formatter("end_datetime"),
        )
        .values_list("code", "end_dates")
    )
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = 'attachment; filename="table.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)

    # Data for the table
    data = [["S.No", "Code", "Valid Upto"]] + [
        [i + 1] + list(voucher_row) for i, voucher_row in enumerate(voucher)
    ]

    table = Table(data)
    voucher_instance_for_second_table = Voucher.objects.filter(voucher_set=voucher_set)
   

    logger.debug(f"{voucher_instance_for_second_table[0].offers.all()=}")
    if (
        voucher_set.voucherset.amount_type
        == "Percentage"
    ):
        voucher_t = "Coupon"
        value_of_offer = (
            voucher_instance_for_second_table[0].offers.all()[0].benefit.value
        )
    elif (
       voucher_set.voucherset.amount_type
        == "Absolute"
    ):
        
        voucher_t = "Absolute" 
        value_of_offer = (
            voucher_instance_for_second_table[0].offers.all()[0].benefit.value
        )
    else:
        voucher_t = "Voucher"
        value_of_offer = (
            voucher_instance_for_second_table[0].offers.all()[0].benefit.value
        )
    logger.debug(f"{value_of_offer=}")
    
    for single_offer in voucher_instance_for_second_table[0].offers.all():

        try:
            if single_offer.benefit.range.back_range:
                proxy_obj = single_offer.benefit.range.back_range
                included_categories = proxy_obj.included_categories.all().values_list(
                    "name", flat=True
                )
                logger.debug(included_categories)
                included_attributes = proxy_obj.attr.all().values_list(
                    "option", flat=True
                )
                include_category_chunks = [
                    ", ".join(included_categories[i : i + 1])
                    for i in range(0, len(included_categories), 1)
                ]
                included_attributes_chunks = [
                    ", ".join(included_attributes[i : i + 1])
                    for i in range(0, len(included_attributes), 1)
                ]
        except Exception as e:
            included_categories = (
                single_offer.condition.range.included_categories.all().values_list(
                    "name", flat=True
                )
            )
            include_category_chunks = [
                ", ".join(included_categories[i : i + 1])
                for i in range(0, len(included_categories), 1)
            ]
            included_attributes_chunks = ["-"]

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="WhiteText", textColor=colors.white))

    table1_data = [
        [
            Paragraph(f"Voucher", styles["WhiteText"]),
            # Paragraph("Category", styles["WhiteText"]),
            # Paragraph("Attributes", styles["WhiteText"]),
            Paragraph("Type", styles["WhiteText"]),
            Paragraph("GST", styles["WhiteText"]),
            Paragraph("Shipping", styles["WhiteText"]),
            # Paragraph("Value", styles["WhiteText"]),
            # Paragraph("Clubable Upto", styles["WhiteText"]),
            # Paragraph("Valid Upto", styles["WhiteText"]),

        ]
    ]

    # if Vou.objects.get(voucher=voucher_set).voucher_type == "Shopping Voucher - Gst Exclusive" or Vou.objects.get(
    #         voucher=voucher_set).voucher_type == "Shopping Voucher - Gst Inclusive":
    #     voucher_data = "Shopping Voucher"
    # else:
    #     voucher_data = "Gift Voucher"

    voucher_instance = Vou.objects.get(voucher=voucher_set)

    # Determine the type of voucher
    shopping_types = [
        "Shopping Voucher - Gst Exclusive",
        "Shopping Voucher - Exclusive",
        "Shopping Voucher - Gst Inclusive",
        "Shopping Voucher - Inclusive"
    ]

    # gift_types = [
    #     "Gift Voucher - Gst Exclusive",
    #     "Gift Voucher - Exclusive",
    #     "Gift Voucher - Gst Inclusive",
    #     "Gift Voucher - Inclusive"
    # ]

    if voucher_instance.voucher_type in shopping_types:
        voucher_data = "Shopping"
    else:
        voucher_data = "Gift"

    # Determine GST data
    gst_data = "Gst Inclusive" if voucher_instance.voucher_type in [
        "Gift Voucher - Inclusive",
        "Shopping Voucher - Inclusive"
    ] else "Gst Exclusive"

    # Determine club data
    club_data = "Clubable" if voucher_instance.clubable else "Non Clubable"

    if voucher_instance.voucher_type == "Gift Voucher - Inclusive" or voucher_instance.voucher_type == "Gift Voucher - Exclusive":
        if voucher_instance.is_ship_charge:
            if voucher_instance.shipping_charges > 0:
                shipping_data = "Fixed"
            else:
                shipping_data = "Free"
        else:
            shipping_data = "Payable"
    else:
        if voucher_instance.is_ship_charge:
            shipping_data = "Fixed"
        elif voucher_instance.is_shipping_included:
            shipping_data = "Inclusive"
        else:
            shipping_data = "Payable"



    if voucher_t == "Coupon" or voucher_t == 'Absolute':

        table1_data.append(
            [
                Paragraph("Discount", styles["Normal"]),
                # Paragraph("\n".join(include_category_chunks), styles["Normal"]),
                # Paragraph("\n".join(included_attributes_chunks), styles["Normal"]),
                # Paragraph("Coupon offer", styles["Normal"]),
                Paragraph(club_data, styles["Normal"]),# this is type field
                Paragraph(gst_data, styles["Normal"]),
                Paragraph(shipping_data, styles["Normal"]),
                # Paragraph(f"{value_of_offer}%", styles["Normal"]),
                # Paragraph(voucher_instance.club_number, styles["Normal"]),
                # Paragraph(voucher_instance.voucher.end_datetime.strftime('%d/%m/%Y'), styles["Normal"]),

            ]
        )
    else:
        table1_data.append(
            [
                Paragraph(voucher_data, styles["Normal"]),
                # Paragraph("\n".join(include_category_chunks), styles["Normal"]),
                # Paragraph("\n".join(included_attributes_chunks), styles["Normal"]),
                # Paragraph("Coupon offer", styles["Normal"]),
                Paragraph(club_data, styles["Normal"]),  # this is type field
                Paragraph(gst_data, styles["Normal"]),
                Paragraph(shipping_data, styles["Normal"]),
                # Paragraph(f"{value_of_offer}%", styles["Normal"]),
                # Paragraph(voucher_instance.club_number, styles["Normal"]),
                # Paragraph(voucher_instance.voucher.end_datetime.strftime('%d/%m/%Y'), styles["Normal"]),
            ]
        )

    table1 = Table(table1_data)

    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), "#230BB2"),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
    )

    table1.setStyle(style)

    table.setStyle(style)

    spacer = Spacer(20, 20)

    # Applying Heading2 style directly to the field names and Normal style to the values
    if voucher_t == "Coupon":
        value_paragraph = Paragraph(f"<b>Value Per Voucher : </b>  {int(value_of_offer)}% of each item", styles["Normal"])
    elif voucher_t == "Absolute":
        value_paragraph = Paragraph(f"<b>Value Per Voucher : </b> Rs {int(value_of_offer)} from each item", styles["Normal"])
    else:
        value_paragraph = Paragraph(f"<b>Value Per Voucher : </b> Rs {int(value_of_offer)}", styles["Normal"])
    clubable_paragraph = Paragraph(f"<b>Clubable Upto : </b> {voucher_instance.club_number}", styles["Normal"])
    valid_upto_paragraph = Paragraph(f"<b>Valid Upto : </b> {voucher_instance.voucher.end_datetime.strftime('%d/%m/%Y %I:%M:%S %p')}", styles["Normal"])

    Category = get_model("catalogue", "Category")
    all_categories = list(Category.objects.all().values_list("name", flat=True))

    include_category_chunks_set = set(include_category_chunks)
    all_categories_set = set(all_categories)

    if not include_category_chunks:
        valid_category_paragraph = Paragraph(f"<b>Product Categories : </b> All", styles["Normal"])
    elif include_category_chunks_set == all_categories_set:
        valid_category_paragraph = Paragraph(f"<b>Product Categories : </b> All", styles["Normal"])
    else:
        valid_category_paragraph = Paragraph(f"<b>Product Categories : </b> {', '.join(include_category_chunks)}",
                                             styles["Normal"])

    # Description remains the same
    title_paragraph = Paragraph("Terms & Conditions : ", styles["Heading2"])

    # Assuming the description is obtained from the voucher object
    voucher_description = Vou.objects.get(voucher=voucher_set).voucher.description

    # Split the description into individual sentences by separating at the comma followed by a single quote.
    description_sentences = voucher_description.strip("[]").split("', '")

    # Removing any leading/trailing quotes from the sentences
    description_sentences = [sentence.strip("' ") for sentence in description_sentences]

    # Formatting each sentence as a paragraph with a bullet
    description_paragraphs = ["• " + sentence for sentence in description_sentences]

    # Convert each formatted sentence into a Paragraph object
    description_flowable = [Paragraph(desc, styles["Normal"]) for desc in description_paragraphs]

    # Build the PDF document with the table, spacer, title, and description flowable
    doc.build(
        [table1, spacer, value_paragraph, clubable_paragraph, valid_upto_paragraph,
         valid_category_paragraph, spacer, title_paragraph] + description_flowable + [spacer,table])

    pdf_bytes = response.content

    password = "admin@123"
    protected_pdf_bytes = password_protect_pdf(pdf_bytes, password)

    response = HttpResponse(protected_pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="table.pdf"'

    return response, protected_pdf_bytes


class VoucherSetDOwnload(VoucherSetDownloadView):
    template_name = "oscar/dashboard/vouchers/voucher_set_for.html"
    model = VoucherSets
    form_class = VoucherSetForm

    def get(self, request, *args, **kwargs):

        voucher_set = self.get_object()

        response, pdf_bytes = generate_pdf(voucher_set=voucher_set)

        return response


from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import io


def password_protect_pdf(pdf_bytes, password):
    output_pdf = io.BytesIO()
    pdf_writer = PdfWriter()
    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))

    for page_num in range(len(pdf_reader.pages)):
        pdf_writer.add_page(pdf_reader.pages[page_num])

    pdf_writer.encrypt(user_password=password, owner_password=None, use_128bit=True)

    pdf_writer.write(output_pdf)
    return output_pdf.getvalue()


from django.shortcuts import redirect, reverse


class VoucherSetSendMailView(VoucherSetDownloadView):
    template_name = "oscar/dashboard/vouchers/voucher_set_for.html"
    model = VoucherSets
    form_class = VoucherSetForm

    def get(self, request, *args, **kwargs):
        voucher_set = self.get_object()
        voucher_user = VoucherSet.objects.get(voucher=voucher_set).user
        response, pdf_bytes = generate_pdf(voucher_set=voucher_set)
        email = EmailMessage(
            "Voucher code pdf",
            "Here is the Voucher code from Oneupbrand",
            "sender@example.com",
            [voucher_user.email],
        )
        pk = kwargs["pk"]
        url = reverse("voucher-detail", kwargs={"pk": pk})

        email.attach("table.pdf", pdf_bytes, "application/pdf")
        email.send()
        return redirect(url)


from oscar.apps.dashboard.vouchers.views import (
    VoucherSetListView as BaseVoucherSetListView,
)


class VoucherSetListView(BaseVoucherSetListView):
    model = VoucherSet
    context_object_name = "voucher_sets"
    template_name = "oscar/dashboard/vouchers/voucher_set_list.html"
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def get_queryset(self):
        qs = self.model.objects.all().order_by("-date_created")
        qs = sort_queryset(
            qs,
            self.request,
            ["num_basket_additions", "num_orders", "date_created"],
            "-date_created",
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        description = _("Voucher sets")
        ctx["description"] = description
        return ctx


import csv
from oscar.apps.voucher.models import Voucher
from django.utils.dateformat import format
from django.utils.timezone import localtime
import csv
import io
import pyzipper
from django.http import HttpResponse
from django.utils.timezone import localtime
from openpyxl import Workbook
class VoucherSetCSVFileDownloadView(View):
    def get(self, request, pk, **kwargs):
        # Fetch the voucher set
        voucher_sets = VoucherSet.objects.get(voucher_id=pk)
        voucher_set_new = VoucherSets.objects.get(id=voucher_sets.voucher_id)
        vouchers = Voucher.objects.filter(voucher_set_id=voucher_sets.voucher_id)
        first_voucher = vouchers.first()

        local_start_datetime = localtime(voucher_set_new.start_datetime).strftime('%d/%m/%Y %H:%M')
        local_end_datetime = localtime(voucher_set_new.end_datetime).strftime('%d/%m/%Y %H:%M')
        local_create_datetime = localtime(voucher_set_new.date_created).strftime('%d/%m/%Y %H:%M')

        # Create an Excel file in memory
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Voucher Data"

        # Write headers in the first row
        worksheet.append([
            "Voucher Name", "User Email", "Voucher Type", "Start DateTime",
            "End DateTime", "Description", "Number Of Vouchers", "Number Of Voucher Type",
            "Status", "Created Date", "Usage"
        ])

        # Write data in the second row
        worksheet.append([
            voucher_set_new.name,
            voucher_sets.user.email,
            voucher_sets.voucher_type,
            local_start_datetime,
            local_end_datetime,
            voucher_set_new.description,
            voucher_set_new.count,
            first_voucher.offers.count(),
            'Active' if first_voucher.is_active else 'Inactive',
            local_create_datetime,
            first_voucher.get_usage_display()
        ])

        # Add the new columns in the third row
        worksheet.append([
            "Code", "Valid Upto"
        ])
        
        for single_voucher in voucher_sets.voucher.vouchers.all():
            single_voucher_end_time = localtime(single_voucher.end_datetime).strftime('%d/%m/%Y %H:%M')
            worksheet.append([
            single_voucher.code, single_voucher_end_time
        ])

        # Save Excel to a BytesIO object
        excel_buffer = io.BytesIO()
        workbook.save(excel_buffer)
        excel_buffer.seek(0)

        # Create a zip file in memory with password protection
        zip_buffer = io.BytesIO()
        with pyzipper.AESZipFile(zip_buffer, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zip_file:
            zip_file.setpassword(b'admin@123')  # Set your desired password here
            zip_file.writestr(f'{voucher_set_new.name}_vouchers.xlsx', excel_buffer.getvalue())
        
        zip_buffer.seek(0)

        # Create the HttpResponse object with the appropriate ZIP header
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{voucher_set_new.name}_vouchers.zip"'

        return response
    