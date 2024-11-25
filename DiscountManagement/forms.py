from django import forms
from apps.catalogue.models import Category


# class DiscountManagementForm(forms.Form):
#     DISCOUNT_TYPE_CHOICES = (
#         ('percentage', 'Percentage'),
#         ('amount', 'Amount'),
#     )

#     discount_type = forms.ChoiceField(choices=DISCOUNT_TYPE_CHOICES, required=True)
#     discount_amount = forms.DecimalField(decimal_places=2, max_digits=12, required=True)

#     apply_to_all_categories = forms.BooleanField(required=False, initial=False)

#     selected_category = forms.ModelChoiceField(
#         queryset=Category.objects.all(), required=False, empty_label='Select a category'
#     )

#     selected_subcategories = forms.ModelMultipleChoiceField(
#         queryset=Category.objects.none(),  # Empty queryset initially
#         required=False,
#         widget=forms.CheckboxSelectMultiple,
#     )

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Dynamically generate choices for selected_subcategories
#         subcategory_choices = [(category.id, category.name) for category in Category.objects.all()]
#         self.fields['selected_subcategories'].choices = subcategory_choices

#     def clean(self):
#         cleaned_data = super().clean()
#         selected_category = cleaned_data.get('selected_category')
#         selected_subcategories = cleaned_data.get('selected_subcategories')

#         if selected_category and cleaned_data.get('apply_to_all_categories'):
#             # If "Apply to all subcategories" is selected, set all subcategories as selected
#             cleaned_data['selected_subcategories'] = selected_category.get_descendants(include_self=True)

#         return cleaned_data


class DiscountManagementForm(forms.Form):
    DISCOUNT_TYPE_CHOICES = (
        ("percentage", "Percentage"),
        ("amount", "Amount"),
    )

    discount_type = forms.ChoiceField(choices=DISCOUNT_TYPE_CHOICES, required=True)
    discount_amount = forms.DecimalField(decimal_places=2, max_digits=12, required=True)

    apply_to_all_categories = forms.BooleanField(required=False, initial=False)

    selected_categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def clean(self):
        cleaned_data = super().clean()
        selected_categories = cleaned_data.get("selected_categories")

        if selected_categories and cleaned_data.get("apply_to_all_categories"):
            # If "Apply to all categories" is selected, set all subcategories as selected
            cleaned_data["selected_subcategories"] = Category.objects.filter(
                tree_id__in=selected_categories.values_list("tree_id", flat=True),
                level__gte=min(selected_categories.values_list("level", flat=True)),
            )

        return cleaned_data
