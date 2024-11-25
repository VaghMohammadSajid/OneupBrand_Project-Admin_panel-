from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from .models import Bannermanagement
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    Bannermanagement,
    CategoryPromotion,
    CategoryPromotionSet,
    VoucherRequestUser,
)
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
import uuid
from DiscountManagement.models import ProxyClassForRange
from .serializers import (
    BannermanagementSerializer,
    CategoryPromotionSerializer,
    VoucherRequestUserSerializer,
)
from rest_framework.permissions import IsAdminUser
from django.http import HttpResponseRedirect, JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.db.models import Q

# for featch the Category for frond end side
from apps.catalogue.models import Category
from .serializers import CategorySerializer, ProductSerializer, LatestProductSerializer
from oscar.apps.partner.strategy import Selector

from apps.catalogue.models import Product
from homepageapi.views import GetProductDetailIdWise
from oscar.core.loading import get_model
from django.urls import reverse

from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from mycustomapi.models import *
from .models import vo
import re
from django.utils.translation import gettext_lazy as _
from useraccount.models import ClientDetails
from django.utils import timezone
from datetime import datetime, time
from .utils import generate_unique_string
from .models import FixedVoucherCondition



def get_subcategories(request):
    category_id = request.GET.get("category_id")
    subcategories = []

    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            subcategories = category.subcategories.all()
        except Category.DoesNotExist:
            pass

    # Create HTML options for subcategories
    options = '<option value="" selected>Select a subcategory</option>'
    for subcategory in subcategories:
        options += f'<option value="{subcategory.id}">{subcategory.name}</option>'

    return JsonResponse({"options": options})


# use to add banner from dashboard
@permission_classes([IsAuthenticated])
class AddBannerView(View):
    template_add_banner = "Banner/Add_banner.html"

    def get(self, request):

        categories = Category.objects.filter(depth=1)
        return render(request, self.template_add_banner, {"categories": categories})

    def post(self, request):
        try:
            title = request.POST.get("title", "")
            active = request.POST.get("active", False) == "on"
            category_id = request.POST.get("category1", None)
            child_category_id = request.POST.get("sub_category1", None)
            link = request.POST.get("Link", "")

            if child_category_id:
                category_id = int(child_category_id)
                category = Category.objects.get(id=category_id)
            elif category_id:
                category_id = int(category_id)
                category = Category.objects.get(id=category_id)
            else:
                category = None

            if request.method == "POST" and request.FILES.get("image"):
                image = request.FILES["image"]

            if request.method == "POST" and request.FILES.get("logo"):
                logo = request.FILES["logo"]

                banner = Bannermanagement.objects.create(
                    image=image,
                    title=title,
                    active=active,
                    category=category,
                    logo=logo,
                    link=link,
                )

                return redirect("banner-list")

        except Exception as e:
            print(str(e))
        return redirect("banner-list")

    @staticmethod
    def get_child_categories(request):
        if request.method == "GET":
            parent_category_id = request.GET.get("parent_category_id")
            parent_category = Category.objects.get(id=parent_category_id)
            child_categories = parent_category.get_descendants()

            # Convert categories to a format suitable for JSON response
            categories_data = [
                {"id": category.id, "name": category.name}
                for category in child_categories
            ]

            return JsonResponse(categories_data, safe=False)


# use to show avilabile banners from dashboard
@permission_classes([IsAuthenticated])
class BannerListView(View):

    template_show_banner = "Banner/banner_list.html"

    def get(self, request):
        banners = Bannermanagement.objects.order_by("-current_date")
        return render(request, self.template_show_banner, {"banners": banners})


# to change to banner active and in active
@permission_classes([IsAuthenticated])
class ToggleBannerView(View):
    def post(self, request, banner_id):
        banner = get_object_or_404(Bannermanagement, pk=banner_id)
        banner.active = not banner.active
        banner.save()

        return redirect("banner-list")


# to change the property of existing banner
@permission_classes([IsAuthenticated])
class EditBannerView(View):

    template_name = "Banner/edit_banner.html"

    def get(self, request, banner_id):

        banner = get_object_or_404(Bannermanagement, pk=banner_id)
        if banner.category:

            c = None
            has_parent = banner.category.get_parent()

            if has_parent:
                has_parent = Category.objects.get(pk=has_parent.id)
            else:
                has_parent = Category.objects.get(pk=11)

        else:
            has_parent = None

        banner_link = banner.link if banner.link else None

        print(banner_link)

        categories = Category.objects.filter(depth=1)

        return render(
            request,
            self.template_name,
            {
                "banner": banner,
                "categories": categories,
                "has_parent": has_parent,
                "banner_link": banner_link,
            },
        )

    def post(self, request, banner_id):
        banner = get_object_or_404(Bannermanagement, pk=banner_id)
        categories = Category.objects.all()

        banner.title = request.POST.get("title", banner.title)
        # banner.category = Category.objects.get(pk=request.POST.get('category'))
        banner.active = bool(request.POST.get("active", False))
        child_category_id = request.POST.get("sub_category1", None)
        category = request.POST.get("category1", None)
        link_value = request.POST.get("link", None)
        banner.current_date = timezone.now()

        print(category, "categname")
        print(child_category_id, "chaild name")
        print(link_value, "test link")

        if child_category_id:
            banner.category = Category.objects.get(pk=request.POST.get("sub_category1"))
            banner.link = None

        elif category:
            banner.category = Category.objects.get(pk=request.POST.get("category1"))
            banner.link = None

        if request.FILES.get("image"):
            banner.image = request.FILES["image"]
        if request.FILES.get("logo"):
            banner.logo = request.FILES["logo"]
        if link_value:
            banner.link = link_value
            banner.category = None

        banner.save()

        return redirect("banner-list")


# use to delete avilabile banners from dashboard
@permission_classes([IsAuthenticated])
class DeleteBannerView(View):

    def post(self, request, pk):
        banner = get_object_or_404(Bannermanagement, pk=pk)
        banner.delete()
        return redirect("banner-list")


# This BannermanagementAPIView is for use front end side
# @permission_classes([IsAuthenticated])
class BannermanagementAPIView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            banners = Bannermanagement.objects.filter(active=True)
            serializer = BannermanagementSerializer(banners, many=True)

            # Manually modify the serialized data to include category hierarchy
            serialized_data = []
            for banner_data in serializer.data:
                category_id = banner_data.get("category")
                category_name = (
                    Category.objects.get(id=category_id).name if category_id else None
                )

                if category_name:
                    # Manually construct the category hierarchy
                    category_hierarchy = [category_name]

                    # Check if the category has a parent
                    category = Category.objects.get(id=category_id)
                    while category.get_parent():
                        category = category.get_parent()
                        category_hierarchy.insert(0, category.name)

                    banner_data["breadcrumbs"] = " > ".join(category_hierarchy)
                else:
                    banner_data["breadcrumbs"] = None

                serialized_data.append(banner_data)

            # Return the modified serialized data
            return Response(serialized_data)

        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# This Api for featch the 3 or 6 Categories. for category promotion
# @permission_classes([IsAuthenticated])
class CategoryPromotions(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Retrieve all active CategoryPromotionSet instances
            promotion_sets = CategoryPromotionSet.objects.filter(is_active=True)

            # Prepare the response structure
            response_data = []

            # Iterate over each CategoryPromotionSet
            for promotion_set in promotion_sets:
                # Retrieve promotions for the current promotion_set
                promotions = CategoryPromotion.objects.filter(set_name=promotion_set)

                # Serialize the promotions
                serializer = CategoryPromotionSerializer(promotions, many=True)

                # Manually modify the serialized data to include category hierarchy and set name
                serialized_data = []
                for promotion_data in serializer.data:
                    category_id = promotion_data.get("category")
                    category_name = (
                        Category.objects.get(id=category_id).name
                        if category_id
                        else None
                    )

                    if category_name:
                        # Manually construct the category hierarchy
                        category_hierarchy = [category_name]

                        # Check if the category has a parent
                        category = Category.objects.get(id=category_id)
                        while category.get_parent():
                            category = category.get_parent()
                            category_hierarchy.insert(0, category.name)

                        promotion_data["breadcrumbs"] = " > ".join(category_hierarchy)
                    else:
                        promotion_data["breadcrumbs"] = None

                    serialized_data.append(promotion_data)

                # Create a dictionary for the current promotion_set with its promotions
                promotion_set_data = {
                    "name": promotion_set.name,
                    "promotions": serialized_data,
                }

                # Append to the response data
                response_data.append(promotion_set_data)

            # Return the final response
            return Response(response_data)

        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


from django.views import View


class ListGSTGroup(View):
    def get(self, request):
        gst_list = GSTGroup.objects.all().order_by("-updated_date")

        context = {
            "gst_list": gst_list,
        }
        return render(request, "taxes/gst_group_list.html", context)


class AddGSTGroup(View):
    template_name = "taxes/gst_group.html"

    def get(self, request):
        gst_list = GSTGroup.objects.all().order_by("gst_group_code")

        context = {
            "gst_list": gst_list,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        gst_group_code = request.POST.get("gst_group_code")
        description = request.POST.get("description")
        rate = request.POST.get("rate")
        user = request.user

        # Validation
        gst_code_error = ""
        if not gst_group_code:
            gst_code_error = "Gst Code is required."

        description_error = ""
        if not description:
            description_error = "Description is required."

        rate_error = ""
        if not rate:
            rate_error = "Rate is required."
        elif not re.match(r"^\d+(\.\d+)?$", rate):
            rate_error = "Rate must be a number."

        if gst_code_error or description_error or rate_error:
            return render(
                request,
                "taxes/gst_group.html",
                {
                    "gst_code_error": gst_code_error,
                    "description_error": description_error,
                    "rate_error": rate_error,
                    "gst_group_code": gst_group_code,
                    "description": description,
                    "rate": rate,
                },
            )
        else:
            # Check if the rate already exists
            if GSTGroup.objects.filter(rate=rate).exists():
                messages.error(request, "Rate already exists.")
            else:
                # Create the GSTGroup object
                GSTGroup.objects.create(
                    gst_group_code=gst_group_code,
                    description=description,
                    rate=rate,
                    created_by=user,
                    updated_by=user,
                )
                messages.success(request, "GST Group created successfully.")

        # Retrieve and pass the updated list of GST groups to the template
        gst_list = GSTGroup.objects.all().order_by("gst_group_code")
        context = {
            "gst_list": gst_list,
        }
        return render(request, self.template_name, context)


class GSTGroupUpdateView(View):
    template_name = "taxes/update_gst_gruop.html"

    def get(self, request, pk):
        edit_gst_list = GSTGroup.objects.get(pk=pk)

        return render(request, self.template_name, {"edit_gst_list": edit_gst_list})

    def post(self, request, pk):

        gst_group_code = request.POST["gst_group_code"]
        description = request.POST["description"]
        rate = request.POST["rate"]
        user = request.user

        # Validation
        gst_code_error = ""
        if not gst_group_code:
            gst_code_error = "Gst Code is required."

        description_error = ""
        if not description:
            description_error = "Description is required."

        rate_error = ""
        if not rate:
            rate_error = "Rate is required."
        elif not re.match(r"^\d+(\.\d+)?$", rate):
            rate_error = "Rate must be a number."

        if gst_code_error or description_error or rate_error:
            return render(
                request,
                "taxes/update_gst_gruop.html",
                {
                    "gst_code_error": gst_code_error,
                    "description_error": description_error,
                    "rate_error": rate_error,
                    "gst_group_code": gst_group_code,
                    "description": description,
                    "rate": rate,
                },
            )
        else:

            gst_data = GSTGroup.objects.filter(id=pk).first()
            gst_data.gst_group_code = gst_group_code
            gst_data.description = description
            gst_data.rate = rate
            gst_data.updated_date = timezone.now()
            gst_data.save()

            gst_list = GSTGroup.objects.all().order_by("gst_group_code")

            context = {
                "gst_list": gst_list,
            }
            messages.success(
                request, _(f'GstCode "{gst_data.gst_group_code}" edit successfully')
            )
            return render(request, "taxes/gst_group_list.html", context)


class GSTGroupDeleteView(View):
    def get(self, request, pk):
        delete_gst_list = GSTGroup.objects.get(pk=pk)
        delete_gst_list.delete()
        messages.success(request, "Gst Code successfully deleted!")
        return redirect("gst-group-list")


class ListGSTSetup(View):
    def get(self, request, *args, **kwargs):
        gst_list = GSTGroup.objects.all().order_by("-updated_date")

        gst_setup = GSTSetup.objects.all().order_by("-updated_date")

        context = {"gst_list": gst_list, "gst_setup": gst_setup}
        return render(request, "taxes/gstsetup_list.html", context)


class AddGSTSetup(View):
    template_name = "taxes/gstsetup.html"

    def get(self, request, *args, **kwargs):

        gst_list = GSTGroup.objects.all()

        gst_setup = GSTSetup.objects.all()

        context = {"gst_list": gst_list, "gst_setup": gst_setup}

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        hsn_code = request.POST["hsn_code"]
        hsn_description = request.POST["hsn_description"]
        print(hsn_description, "hsn_descriptionhsn_description")
        rate = request.POST["gst_rate"]

        user = request.user

        # Validation
        gst_code_error = ""
        if not hsn_code:
            gst_code_error = "Hsn Code is required."

        description_error = ""
        if not hsn_description:
            description_error = "Hsn Description is required."

        if gst_code_error or description_error:
            return render(
                request,
                "taxes/gstsetup.html",
                {
                    "gst_code_error": gst_code_error,
                    "description_error": description_error,
                    "hsn_code": hsn_code,
                    "hsn_description": hsn_description,
                    "rate": rate,
                },
            )
        else:

            if GSTSetup.objects.filter(hsn_code__iexact=hsn_code).exists():
                pass
            else:
                GSTSetup.objects.create(
                    hsn_code=hsn_code,
                    hsn_description=hsn_description,
                    gst_rate_id=rate,
                    created_by=user,
                    updated_by=user,
                )

            gst_setup = GSTSetup.objects.all()

            context = {"gst_setup": gst_setup}
        return render(request, self.template_name, context)


class GSTSetupUpdateView(View):
    template_name = "taxes/update_gstsetup.html"

    def get(self, request, pk):
        edit_gstSetup_list = GSTSetup.objects.get(pk=pk)
        edit_gstGroup_list = GSTGroup.objects.all()

        return render(
            request,
            self.template_name,
            {
                "edit_gstSetup_list": edit_gstSetup_list,
                "edit_gstGroup_list": edit_gstGroup_list,
            },
        )

    def post(self, request, pk):
        hsn_code = request.POST["hsn_code"]
        hsn_description = request.POST["hsn_description"]
        gst_rate_id = request.POST["gst_rate"]

        # Validation
        gst_code_error = ""
        if not hsn_code:
            gst_code_error = "Hsn Code is required."

        description_error = ""
        if not hsn_description:
            description_error = "Hsn Description is required."

        if gst_code_error or description_error:
            return render(
                request,
                "taxes/update_gstsetup.html",
                {
                    "gst_code_error": gst_code_error,
                    "description_error": description_error,
                    "hsn_code": hsn_code,
                    "hsn_description": hsn_description,
                    "gst_rate": gst_rate_id,
                },
            )
        else:

            gstsetup_data = get_object_or_404(GSTSetup, pk=pk)
            gstgroup_data = get_object_or_404(GSTGroup, pk=gst_rate_id)

            gstsetup_data.hsn_code = hsn_code
            gstsetup_data.hsn_description = hsn_description
            gstsetup_data.gst_rate = gstgroup_data
            gstsetup_data.save()

            gst_setup = GSTSetup.objects.all().order_by("hsn_code")

            context = {
                "gst_setup": gst_setup,
            }
            messages.success(
                request, _(f'GstSetup "{gstsetup_data.hsn_code}" edit successfully')
            )
            return render(request, "taxes/gstsetup_list.html", context)


class GSTSetupDeleteView(View):
    def get(self, request, pk):
        delete_gst_list = GSTGroup.objects.get(pk=pk)
        delete_gst_list.delete()
        messages.success(request, "Gst Code successfully deleted!")
        return redirect("gst-setup-list")


def get_product_price(product):
    try:
        strategy = Selector().strategy()
        info = strategy.fetch_for_product(product)
        return info.price.excl_tax
    except ObjectDoesNotExist:
        return None


# @permission_classes([IsAuthenticated])

from rest_framework.generics import ListAPIView

from oscar.core.loading import get_model

Product = get_model("catalogue", "Product")


class LatestProductAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Product.objects.filter(
        Q(structure="child") & Q(is_public=True)
    ).order_by("-date_created")[:50]
    serializer_class = LatestProductSerializer


# this is for add  category promotion banners
@method_decorator(staff_member_required, name="dispatch")
class AddCategoryPromotion(View):
    template_add_banner = "Banner/Add_CategoryPromotion.html"

    def get(self, request):
        categories = Category.objects.filter(depth=1)
        return render(request, self.template_add_banner, {"categories": categories})

    def post(self, request):
        try:
            set_name = request.POST.get("setName")
            set_is_active = request.POST.get("setIsActive", False) == "on"

            category_promotion_set = CategoryPromotionSet.objects.create(
                name=set_name,
                is_active=set_is_active,
            )

            num_sets = 3

            for i in range(1, num_sets + 1):
                image_key = f"image{i}"
                category_key = f"category{i}"
                sub_category_key = f"sub_category{i}"  # Added subcategory key
                title_key = f"title{i}"
                Link_key = f"Link{i}"

                image = request.FILES.get(image_key)
                category_id = request.POST.get(category_key)
                sub_category_id = request.POST.get(sub_category_key)
                title = request.POST.get(title_key, "")
                Link = request.POST.get(Link_key, "")

                if sub_category_id:
                    category_id = int(sub_category_id)
                    category = Category.objects.get(id=category_id)
                elif category_id:
                    category_id = int(category_id)
                    category = Category.objects.get(id=category_id)
                else:
                    category = None

                if Link or category:
                    # Create the CategoryPromotion object with the provided data
                    banner = CategoryPromotion.objects.create(
                        image=image,
                        title=title,
                        category=category,
                        set_name=category_promotion_set,
                        Link=Link,
                    )

            return redirect("CategoryPromotionList-list")

        except Exception as e:
            print(str(e))
            return redirect("CategoryPromotionList-list")


class EditCategoryPromotion(View):
    template_edit_banner = "Banner/Edit_CategoryPromotion.html"

    def get(self, request, pk):
        promotion_set = get_object_or_404(CategoryPromotionSet, pk=pk)
        categories = Category.objects.filter(depth=1)
        category_promotions = CategoryPromotion.objects.filter(set_name=promotion_set)

        category_info = []
        for promotion in category_promotions:
            if promotion.category:
                category_name = promotion.category.name
                parent_names = []

                # Fetch parent categories recursively
                parent_category = (
                    promotion.category.get_parent()
                )  # Adjust to your actual method to get parent
                while parent_category:
                    parent_names.append(parent_category.name)
                    parent_category = (
                        parent_category.get_parent()
                    )  # Adjust to your actual method to get parent

                category_info.append(
                    {"category_name": category_name, "parent_names": parent_names}
                )

                print(f"Category Name: {category_name}, Parent Names: {parent_names}")

        return render(
            request,
            self.template_edit_banner,
            {
                "promotion_set": promotion_set,
                "categories": categories,
                "category_info": category_info,  # Pass category info to template
            },
        )

    def post(self, request, pk):
        try:
            promotion_set = get_object_or_404(CategoryPromotionSet, pk=pk)
            promotion_set.name = request.POST.get("setName")
            promotion_set.is_active = request.POST.get("setIsActive", False) == "on"
            promotion_set.save()

            for i, banner in enumerate(
                promotion_set.categorypromotion_set.all(), start=1
            ):
                image_key = f"image{i}"
                category_key = f"category{i}"
                sub_category_key = f"sub_category{i}"
                title_key = f"title{i}"
                link_key = f"Link{i}"

                image = request.FILES.get(image_key, None)
                existing_image = request.POST.get(f"existing_image{i}")
                category_id = request.POST.get(category_key)
                sub_category_id = request.POST.get(sub_category_key)
                title = request.POST.get(title_key, "")
                link = request.POST.get(link_key, "")

                if sub_category_id:
                    category_id = int(sub_category_id)
                    category = Category.objects.get(id=category_id)
                elif category_id:
                    category_id = int(category_id)
                    category = Category.objects.get(id=category_id)
                else:
                    category = None

                if image:
                    banner.image = image
                elif existing_image:
                    banner.image = existing_image

                banner.category = category
                banner.title = title
                banner.Link = link
                banner.save()

            return redirect("CategoryPromotionList-list")

        except Exception as e:
            print(str(e))
            return redirect("CategoryPromotionList-list")


# in frontend side categ promotion list
@permission_classes([IsAuthenticated])
class CategoryPromotionList(View):

    @method_decorator(staff_member_required(login_url="login"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    template_show_banner = "Banner/CategoryPromotion.html"

    def get(self, request):
        sets = CategoryPromotionSet.objects.all().order_by("-current_date")
        return render(request, self.template_show_banner, {"sets": sets})


# for deletecateg banner once delete that time delete curresponding 3 banners
@permission_classes([IsAuthenticated])
class DeleteCategoryBannerView(View):

    def post(self, request, pk):
        banner = get_object_or_404(CategoryPromotionSet, pk=pk)
        banner.delete()
        return redirect("CategoryPromotionList-list")


# for edit banners
@permission_classes([IsAuthenticated])
class EditCategoryBannerView(View):

    # template_name = 'Banner/edit_banner_categ.html'

    # def get(self, request, banner_id):

    #     banner = get_object_or_404(CategoryPromotion, pk=banner_id)
    #     if  banner.category:

    #         c = None
    #         has_parent = banner.category.get_parent()

    #         if has_parent:
    #             has_parent=Category.objects.get(pk=has_parent.id)
    #         else:
    #             has_parent=Category.objects.get(pk=11)

    #     else:has_parent=None

    #     # if  banner.Link

    #     categories = Category.objects.filter(depth=1)

    #     return render(request, self.template_name, {'banner': banner,'categories': categories,'has_parent':has_parent})

    def post(self, request, banner_id):
        banner = get_object_or_404(CategoryPromotion, pk=banner_id)
        category_promotion_set = banner.set_name

        # Delete the banner
        banner.delete()

        # Check if there are any remaining banners in the set
        if not CategoryPromotion.objects.filter(
            set_name=category_promotion_set
        ).exists():
            category_promotion_set.delete()
            return redirect("CategoryPromotionList-list")

        redirect_url = reverse(
            "open-banner", kwargs={"set_id": category_promotion_set.id}
        )
        return redirect(redirect_url)


# for change active and in active categ banners
@permission_classes([IsAuthenticated])
class ToggleCategoryBannerView(View):

    def post(self, request, banner_id):
        banner = get_object_or_404(CategoryPromotionSet, pk=banner_id)
        banner.is_active = not banner.is_active
        banner.save()

        # Redirect to the banner list view after toggling
        return redirect("CategoryPromotionList-list")


@permission_classes([IsAuthenticated])
class OpenBannerView(View):

    def get(self, request, set_id):
        try:
            category_promotion_set = CategoryPromotionSet.objects.get(id=set_id)
            banners = CategoryPromotion.objects.filter(
                set_name=category_promotion_set
            ).order_by("-current_date")
            return render(
                request,
                "Banner/Openbanners.html",
                {"banners": banners, "set_name": category_promotion_set.name},
            )
        except CategoryPromotionSet.DoesNotExist:
            # Handle the case where the CategoryPromotionSet does not exist
            return render(
                request,
                "Banner/open_banner.html",
                {"error": "CategoryPromotionSet not found"},
            )


# for brand

from django.shortcuts import render, redirect
from .models import Brand
from .forms import BrandForm
from django.db.models import Count
from .models import Brand


def manage_brands(request):
    if request.method == "POST":
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("manage_brands_list")
    else:
        form = BrandForm()

    return render(request, "Banner/manage_brands.html", {"form": form})


class ManageBrandList(View):
    def get(self, request):
        brands = Brand.objects.all().order_by("-current_date")
        return render(request, "Banner/brandLogo_list.html", {"brands": brands})


class EditManageBrand(View):
    def get(self, request, brand_id):
        brand_instance = get_object_or_404(Brand, id=brand_id)
        form = BrandForm(instance=brand_instance)
        return render(
            request, "Banner/edit_brandsLogo.html", {"form": form, "brand_id": brand_id}
        )

    def post(self, request, brand_id):
        brand_instance = get_object_or_404(Brand, id=brand_id)

        form = BrandForm(request.POST, request.FILES, instance=brand_instance)

        if form.is_valid():
            form.instance.current_date = timezone.now()
            form.save()
            return redirect("manage_brands_list")

        return render(
            request, "Banner/edit_brandsLogo.html", {"form": form, "brand_id": brand_id}
        )


class DeleteManageBrand(View):
    def get(self, request, pk):
        brands = Brand.objects.get(pk=pk)
        brands.delete()
        messages.success(request, "Brand Deleted Successfully!")
        return redirect("manage_brands_list")


#############################

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View


# class GSTGroupListView(View):
#     template_name = 'taxes/gst_group.html'

#     def get(self, request):
#         gst_list = GSTGroup.objects.all().order_by("gst_group_code")
#         form = GSTGroupForm()
#         return render(request, self.template_name, {'form': form, 'gst_list': gst_list})

#     def post(self, request):
#         form = GSTGroupForm(request.POST)
#         if form.is_valid():
#             form.save()
#         return redirect('gst-group-list')

# class GSTGroupUpdateView(View):
#     template_name = 'taxes/gst_group_update.html'

#     def get(self, request, pk):
#         gst_group = get_object_or_404(GSTGroup, pk=pk)
#         form = GSTGroupForm(instance=gst_group)
#         return render(request, self.template_name, {'form': form, 'gst_group': gst_group})

#     def post(self, request, pk):
#         gst_group = get_object_or_404(GSTGroup, pk=pk)
#         form = GSTGroupForm(request.POST, instance=gst_group)
#         if form.is_valid():
#             form.save()
#             return redirect('gst-group-list')

# class GSTGroupDeleteView(View):
#     def get(self, request, pk):
#         gst_group = get_object_or_404(GSTGroup, pk=pk)
#         gst_group.delete()
#         return redirect('gst-group-list')


# voucher_sets code bellow
from oscar.apps.voucher.models import Voucher
from .models import VoucherSet
from .utils import Content
# GSTGroup
Voucher = get_model("voucher", "Voucher")


class vouchersets(View):
    template_name = "oscar/dashboard/vouchers/voucher_set_list.html"

    def get(self, request):
        # Fetch all VoucherSets that have related Vouchers
        voucher_sets = (
            VoucherSet.objects.filter(voucher__isnull=False)
            .distinct()
            .order_by("-createDate")
        )

        context = {
            "voucher_sets": voucher_sets,
        }

        return render(request, self.template_name, context)


StockRecord = get_model("partner", "StockRecord")
AttributeOptionGroup = get_model("catalogue", "AttributeOptionGroup")
AttributeOption = get_model("catalogue", "AttributeOption")
Category = get_model("catalogue", "Category")
Product = get_model("catalogue", "Product")
Range = get_model("offer", "Range")
Condition = get_model("offer", "Condition")
Benefit = get_model("offer", "Benefit")
ConditionalOffer = get_model("offer", "ConditionalOffer")
ProductCategory = get_model("catalogue", "ProductCategory")
ProductAttributeValue = get_model("catalogue", "ProductAttributeValue")

OrderDiscount = get_model("order", "OrderDiscount")
Voucher = get_model("voucher", "Voucher")
from mycustomapi.models import GSTGroup
from oscar.apps.voucher.models import Voucher

from django.contrib.auth.models import User
from useraccount.models import ClientDetails
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
# GSTGroup
Voucher = get_model("voucher", "Voucher")
Offer = get_model("offer", "ConditionalOffer")
VoucherSet_Oscar = get_model("voucher", "VoucherSet")
from oscar.apps.voucher.utils import get_unused_code
from bannermanagement.models import RecordCreatedBy
voucher_dict_map = {
    "1":"Gift Voucher - Inclusive",
    "2":"Shopping Voucher - Exclusive",
    "3":"Shopping Voucher - Inclusive",
    "4":"Gift Voucher - Exclusive"
}


class Addvoucher(View):
    template_name = "Voucherset/add_voucherset.html"

    def get(self, request):
        voucher_names = Voucher.objects.all().values_list("name", flat=True)
        if voucher_names:
            main_names = set()
            for name in voucher_names:
                main_name = name.rsplit("-", 1)[0].strip()
                main_names.add(main_name)
        else:
            main_names = []

        

        voucher_types = [
            {"id":"1","name":"Gift Voucher - Gst Inclusive"},
            {"id":"2","name":"Shopping Voucher - Gst Exclusive"},
            {"id":"3","name":"Shopping Voucher - Gst Inclusive"},
            {"id":"4","name":"Gift Voucher - Gst Exclusive"},
        ]

        # Retrieve all client details
        client_details_tuple = ClientDetails.objects.all().values_list(
            "user__id", flat=True
        )
        # retrieve all client user obj
        users = User.objects.filter(is_superuser=False, id__in=client_details_tuple)
        offers = Offer.objects.all().order_by("-start_datetime")
        all_category = Category.objects.all()
        all_attributes = AttributeOptionGroup.objects.all()
        context = {
            "voucher_names": main_names,
            "voucher_types": voucher_types,
            # 'gst_rates': gst_rates,
            "users": users,
            "offers": offers,
            "all_category": all_category,
            "all_attributes": all_attributes
        }
        print("IP Address for debug-toolbar: " + request.META['REMOTE_ADDR'])
        return render(request, self.template_name, context)

    def post(self, request):

        voucher_name = request.POST.get("voucher_name")
        length_of_code = request.POST.get("length_of_code")
        description = request.POST.get("description")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        number_of_voucher = request.POST.get("number_of_voucher")
        user_id = request.POST.get("user")
        amount_type = request.POST.get("amount_type")
        logger.debug(amount_type)
        
        if amount_type == "Percentage" or amount_type == "Absolute":
            voucher_type = "Gift Voucher - Inclusive"
        else:    
            voucher_type = voucher_dict_map.get(request.POST.get("voucher_type"))
        

        offer_apply = request.POST.get("offer")
        shipping_charges = 0
        is_shipping = request.POST.get("shipin_check")
        number_club = request.POST.get("number_club")
        is_club = request.POST.get("is_club")
        is_shipping_included = request.POST.get("is_shipping_included")
        created_by = request.user
        voucher_amount = request.POST.get("voucher_amount")
        
        shipping_type = request.POST.get("shipping_type")
        brand_id: list = request.POST.getlist("brands")

        selected_category = request.POST.getlist("category")

        offer_name = request.POST.get("offer_name")
        offer_name = generate_unique_string()
        

        description = request.POST.get("description")
        description ="its an offer"

        type_of_voucher = "2"
        if type_of_voucher == None:
            messages.error(request, "voucher type req")
            return redirect("add-voucher")
        if type_of_voucher == "1":
            type_of_offer = "Percentage"
        else:
            type_of_offer = "Fixed price"

        value_of_offer = 0

        attr_value = request.POST.getlist("attr_value")
        if len(attr_value) == None:
            messages.error(request, "attribute value required")
            return redirect("add-voucher")
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
            return redirect("add-voucher")
        except:
            messages.error(request=request, message="unexpected error occured")
            return redirect("add-voucher")

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
            logger.error("error in creating voucher",exc_info=True)
            
            messages.error(request=request, message="offer name already exist")
            return redirect("add-voucher")
        except Exception as e:
            logger.error(e)

            messages.error(request=request, message="unexpected error occured")
            return redirect("add-voucher")
        logger.debug(f"{new_conditional_offer.__dict__=}")

        if voucher_type == "Gift Voucher - Inclusive" or  voucher_type ==  "Gift Voucher - Exclusive":  
            length_of_code = 8
        else:
            length_of_code = 10
        logger.debug(length_of_code)
        
        if shipping_type == "0":
            is_shipping = "on"
            shipping_charges = int(request.POST.get("fixed_amount"))
        if shipping_type == "2":
            # import pdb;pdb.set_trace()
            if voucher_type == "Gift Voucher - Inclusive" or voucher_type == "Gift Voucher - Exclusive":
                logger.debug("inside gift if ")
                is_shipping = "on"
                shipping_charges = int(0)
            else:
                logger.debug("inside gift if ")
                is_shipping_included = "on"
        
        # import pdb;pdb.set_trace()


        # Check if the voucher is already assigned to a user

        if is_club and int(number_club) <= 0:
            messages.error(request, "need to have more than 0 if voucher is clubable")
            return redirect("add-voucher")
        voucher_name = offer_name
        if not voucher_name:
            messages.error(request, "Voucher name Required")
            return redirect("add-voucher")

        if not length_of_code:
            messages.error(request, "code length required")
            return redirect("add-voucher")
        if not start_date:
            messages.error(request, "start date required")
            return redirect("add-voucher")
        if not end_date:
            messages.error(request, "end date required")
            return redirect("add-voucher")
        if not number_of_voucher:
            messages.error(request, "Number of voucher required")
            return redirect("add-voucher")

        if is_shipping == "on" and shipping_charges == 0:
            ship=True
        elif is_shipping == "on" and shipping_charges > 0:
             ship="Yes on With Charge"
               
        else:
            ship = False


        if voucher_type in ("Gift Voucher - Inclusive","Shopping Voucher - Inclusive"):
            tax = False
        else:
            tax = True
            

        if voucher_type in ("Gift Voucher - Inclusive","Gift Voucher - Exclusive"):
            voucher=True
        else:
            voucher = False
            if is_shipping_included == "on":
                ship = True
        
        # import pdb;pdb.set_trace()

        if is_club:
            ob = Content(end_date=end_date,clubable=number_club,tax=tax,ship=ship,voucher=voucher,amount=voucher_amount)
        else:
            ob = Content(end_date=end_date,clubable=False,tax=tax,ship=ship,voucher=voucher,amount=voucher_amount)


        
        description = ob.description 
        

        offers = new_conditional_offer

        offers.benefit.value = voucher_amount
        offers.benefit.save()

        start_date_time = start_date
        end_date_time = end_date
        logger.debug(start_date_time)
        logger.debug(end_date_time)
        original_datetime = datetime.strptime(start_date_time, "%Y-%m-%dT%H:%M")
        date_part = original_datetime.date()
        morning_time = datetime.combine(date_part, time.min)
        morning_time_with_timezone = timezone.make_aware(morning_time, timezone.get_current_timezone())
        start_date_time = morning_time_with_timezone

        try:
            voucher_set_oscar = VoucherSet_Oscar.objects.create(
                name=offer_name,
                count=0,
                code_length=length_of_code,
                description=description,
                start_datetime=start_date_time,
                end_datetime=end_date_time,
            )
        except:
            messages.error(request=request, message="there is voucher with same name")
            return redirect("add-voucher")
        for i in range(1, int(number_of_voucher) + 1):
            created_voucher = Voucher.objects.create(
                name=f"{voucher_set_oscar.name}-{i}",
                code=get_unused_code(length=int(length_of_code), separator=""),
                usage="Single use",
                start_datetime=start_date_time,
                end_datetime=end_date_time,
                voucher_set=voucher_set_oscar,
            )
            created_voucher.offers.add(offers)
            created_voucher.save()

        voucher_set_oscar.update_count()

        existing_user_assignment = VoucherSet.objects.filter(
            vouchername=voucher_name, user_id__isnull=False
        ).exists()
        if existing_user_assignment:
            # Add an error message
            messages.error(request, "This voucher is already assigned to a user.")
            return redirect("add-voucher")

        # Check if a voucher with the same user already exists
        existing_voucher_set = VoucherSet.objects.filter(
            vouchername=voucher_name, user_id=user_id
        ).exists()

        if existing_voucher_set:
            # Add an error message
            messages.error(
                request, "This voucher is already associated with the selected team."
            )
            return redirect("add-voucher")

        user = User.objects.get(pk=user_id)
        if is_shipping_included == "on":
            shipping_include = True
        else:
            shipping_include = False
        if is_shipping == "on":
            if is_club == "on":
                voucher_set = VoucherSet.objects.create(
                    vouchername=voucher_name,
                    voucher_type=voucher_type,
                    user=user,
                    shipping_charges=shipping_charges,
                    is_ship_charge=True,
                    clubable=True,
                    club_number=number_club,
                    created_by=created_by,
                    is_shipping_included=shipping_include,
                    amount_type = amount_type,
                    voucher_amount = voucher_amount
                )
            else:
                voucher_set = VoucherSet.objects.create(
                    vouchername=voucher_name,
                    voucher_type=voucher_type,
                    user=user,
                    shipping_charges=shipping_charges,
                    is_ship_charge=True,
                    clubable=False,
                    club_number=0,
                    created_by=created_by,
                    is_shipping_included=shipping_include,
                    amount_type = amount_type,
                    voucher_amount = voucher_amount
                )

        else:
            if is_club == "on":
                voucher_set = VoucherSet.objects.create(
                    vouchername=voucher_name,
                    voucher_type=voucher_type,
                    user=user,
                    shipping_charges=0,
                    is_ship_charge=False,
                    clubable=True,
                    club_number=number_club,
                    created_by=created_by,
                    is_shipping_included=shipping_include,
                    amount_type = amount_type,
                    voucher_amount = voucher_amount
                )
            else:
                voucher_set = VoucherSet.objects.create(
                    vouchername=voucher_name,
                    voucher_type=voucher_type,
                    user=user,
                    shipping_charges=0,
                    is_ship_charge=False,
                    clubable=False,
                    club_number=0,
                    created_by=created_by,
                    is_shipping_included=shipping_include,
                    amount_type = amount_type,
                    voucher_amount = voucher_amount
                )

        if amount_type == "Percentage" or amount_type == "Absolute":
            max_value = request.POST.get("max_input")
            min_value = request.POST.get("min_input")
            FixedVoucherCondition.objects.create(max_value=max_value,min_value=min_value,voucherset=voucher_set)
            
        messages.success(self.request, _("Voucher set successfully created!"))

        return redirect("voucher-sets")


class Editvoucherset(View):
    template_name = (
        "Voucherset/edit_voucherset.html"  # replace with your actual template name
    )

    def get(self, request, *args, voucher_id):
        voucher_set = get_object_or_404(VoucherSet, pk=voucher_id)
        voucher_names = vo.objects.values_list("name", flat=True)
        client_users_query_set = ClientDetails.objects.select_related("user").all()
        users = [client.user for client in client_users_query_set if client.user]
        # users = User.objects.all().filter(is_superuser=False)
        voucher_types = ["Gift Voucher - Inclusive", "Shopping Voucher - Exclusive"]
        # gst_rates = GSTGroup.objects.all()

        context = {
            "voucher_set": voucher_set,
            "voucher_names": voucher_names,
            "users": users,
            "voucher_types": voucher_types,
            # 'gst_rates': gst_rates,
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, voucher_id):
        voucher_set = get_object_or_404(VoucherSet, pk=voucher_id)

        vouchername = request.POST.get("voucher_name")
        user_id = request.POST.get("user")
        voucher_type = request.POST.get("voucher_type")
        # gstrate = request.POST.get('gst_rate')

        user = get_object_or_404(User, pk=user_id)
        voucher_set.vouchername = vouchername
        voucher_set.user = user
        voucher_set.voucher_type = voucher_type
        # voucher_set.gstrate = gstrate
        voucher_set.createDate = timezone.now()

        voucher_set.save()

        messages.success(request, "Voucher set successfully updated!")
        return redirect("voucher-sets")  # replace with your actual URL name


def is_valid_gst_group_code(gst_group_code):
    email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(email_regex, gst_group_code))


class VoucherRequestUserApi(APIView):
    def get(self, request, pk):
        try:
            voucher_data = VoucherRequestUser.objects.filter(user=pk).order_by(
                "-submission_date"
            )
            serializer = VoucherRequestUserSerializer(voucher_data, many=True).data
            return Response({"Voucher Request Data": serializer})
        except VoucherRequestUser.DoesNotExist:
            return Response({"error": "Voucher request user not found."}, status=404)

    def post(self, request, *args, **kwargs):
        select_all_categories = request.data.get("select_all_categories", False)
        categories_id = request.data.get("categories", [])

        request_data = request.data.copy()
        request_data.pop("select_all_categories", None)
        request_data.pop("categories", None)

        serializers = VoucherRequestUserSerializer(data=request_data)
        if serializers.is_valid():
            voucher_request_user = serializers.save()

            if select_all_categories:
                all_category = Category.objects.all()
                voucher_request_user.select_categories.set(all_category)
            else:
                voucher_request_user.select_categories.set(categories_id)
            return Response(serializers.data, status=status.HTTP_201_CREATED)
        return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)


class VoucherRequestUserList(View):
    template_name = "oscar/dashboard/vouchers/voucher_request_user_list.html"

    def get(self, request):
        voucher_requests_data = VoucherRequestUser.objects.all().order_by(
            "-submission_date"
        )
        return render(
            request,
            self.template_name,
            {"voucher_requests_data": voucher_requests_data},
        )


class VoucherRequestUserDelete(View):
    def get(self, request, pk):
        voucher_request_data = VoucherRequestUser.objects.get(pk=pk)
        voucher_request_data.delete()
        messages.success(request, "Voucher Requests Successfully Deleted")
        return redirect("voucher-request-user-list")

from useraccount.models import UniqueStrings
class VoucherRequestUserDetails(View):
    template_name = "oscar/dashboard/vouchers/voucher_request_user_detail.html"

    def get(self, request, pk):
        voucher_details = VoucherRequestUser.objects.get(pk=pk)
        account_id = UniqueStrings.objects.get(user=voucher_details.user)
        all_category = Category.objects.all()
        client_data = ClientDetails.objects.get(user=voucher_details.user)
        selected_categories = (
            voucher_details.select_categories.all()
        )  # Assuming it's a many-to-many field

        # Check if all categories are selected
        if set(selected_categories) == set(all_category):
            context = {
                "voucher_details": voucher_details,
                "category": "All",
                "account_id":account_id.unique_string,
                "company_name": client_data.company_name
            }
        else:
            context = {
                "voucher_details": voucher_details,
                "selected_categories": selected_categories,
                "account_id":account_id.unique_string,
                "company_name": client_data.company_name
            }

        return render(request, self.template_name, context)


class VoucherRequestUserStatus(View):
    def post(self, request, pk):
        voucher_request_data = VoucherRequestUser.objects.get(pk=pk)
        if voucher_request_data:
            status_data = request.POST.get('action')
            if status_data == "Created":
                voucher_request_data.status = "Created"
            elif status_data == "Closed":
                voucher_request_data.status = "Closed"
            else:
                voucher_request_data.status = "Requested"
            voucher_request_data.save()
            messages.success(request, "Voucher Request Status Updated")
        else:
            messages.error(request, "Voucher Request Client Not Found.")
        return redirect(reverse("voucher-request-user-details", kwargs={"pk": pk}))
