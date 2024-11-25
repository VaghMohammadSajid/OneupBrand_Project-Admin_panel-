from django import forms

# from oscar.apps.catalogue.models import ProductAttribute, ProductAttributeValue
from .models import Brand
from oscar.core.loading import get_model


brand_group = get_model("catalogue", "AttributeOptionGroup")

# ProductAttributeValue=get_model('catalogue', 'ProductAttributeValue')
# class BrandForm(forms.ModelForm):
#     class Meta:
#         model = Brand
#         fields = ['attribute', 'attribute_value', 'logo']
#         widgets = {
#             'attribute': forms.Select(attrs={'class': 'form-control'}),
#             'attribute_value': forms.Select(attrs={'class': 'form-control'}),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         # Retrieve all 'Brand' attributes
#         brand_attributes = ProductAttribute.objects.filter(name='Brand').distinct()

#         if brand_attributes.count() == 1:
#             # Only one 'Brand' attribute, use it
#             brand_attribute = brand_attributes.first()

#             # Use .distinct() for filtering attribute_values queryset
#             attribute_values = ProductAttributeValue.objects.filter(attribute=brand_attribute).distinct('value_option__option')
#             self.fields['attribute_value'].queryset = attribute_values
#             self.fields['attribute_value'].label_from_instance = lambda obj: obj.value_option.option

#             # Use .distinct() for filtering attribute queryset
#             self.fields['attribute'].queryset = ProductAttribute.objects.filter(
#                 name='Brand',
#                 id=brand_attribute.id
#             ).distinct()

#         elif brand_attributes.count() > 1:
#             self.fields['attribute'].queryset = brand_attributes
#             self.fields['attribute'].label_from_instance = lambda obj: obj.name

#         else:
#             pass

#         self.fields['logo'].widget = forms.FileInput(attrs={'class': 'form-control','accept': 'image/*'})

#     def clean(self):
#         cleaned_data = super().clean()
#         attribute = cleaned_data.get('attribute')
#         attribute_value = cleaned_data.get('attribute_value')

#         # Ensure that the selected attribute and value match
#         if attribute and attribute_value:
#             if attribute_value.attribute != attribute:
#                 raise forms.ValidationError("Attribute value does not match the selected attribute.")

#         return cleaned_data

# class BrandForm(forms.ModelForm):
#     class Meta:
#         model = Brand
#         fields = ['brand_name','logo']
#         widgets = {
#             'brand_name': forms.Select(attrs={'class': 'form-control'}),

#         }
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         brands = brand_group.objects.get(name="brand")


#         all_brand = brands.options.all()
#         print(all_brand)
#         self.fields['brand_name'].queryset = all_brand
#         self.fields['brand_name'].label_from_instance = lambda obj: obj.option

#         self.fields['logo'].widget = forms.FileInput(attrs={'class': 'form-control','accept': 'image/*'})


class BrandForm(forms.ModelForm):
    brand_name = forms.CharField(
        widget=forms.Select(choices=[
            (option, option) for option in brand_group.objects.get(name="brand").options.values_list('option', flat=True)
        ], attrs={"class": "form-control"}
        ),
    )

    class Meta:
        model = Brand
        fields = ["brand_name", "logo"]
        widgets = {
            "logo": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            )
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

