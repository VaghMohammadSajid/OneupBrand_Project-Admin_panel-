from oscar.apps.dashboard.offers.forms import RestrictionsForm as BaseRestrictionsForm
from oscar.apps.dashboard.offers.forms import BenefitForm as BaseBenefitForm
from django import forms
from django.utils.translation import gettext_lazy as _

from oscar.core.loading import get_model
from oscar.forms import widgets

ConditionalOffer = get_model("offer", "ConditionalOffer")
Benefit = get_model("offer", "Benefit")


class RestrictionsForm(BaseRestrictionsForm):
    start_datetime = forms.DateTimeField(
        widget=widgets.DateTimePickerInput(), label=_("Start date"), required=False
    )
    end_datetime = forms.DateTimeField(
        widget=widgets.DateTimePickerInput(), label=_("End date"), required=False
    )

    class Meta:
        model = ConditionalOffer
        fields = (
            "start_datetime",
            "end_datetime",
            # 'max_basket_applications',
            # 'max_user_applications',
            # 'max_global_applications',
            # 'max_discount',
            # 'priority',
            "exclusive",
            "combinations",
        )


class BenefitForm(BaseBenefitForm):
    class Meta:
        model = Benefit
        fields = (
            "range",
            "type",
            "value",
            # "max_affected_items"
        )
