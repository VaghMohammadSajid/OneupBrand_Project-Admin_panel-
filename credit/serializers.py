from rest_framework import serializers
from .models import CreditRequestUser
import logging

logger = logging.getLogger(__name__)


class CreditRequestUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRequestUser
        fields = "__all__"


from .models import Credit, CreditHistory


class CreditHistorySerializer(serializers.ModelSerializer):
    order_number = serializers.SerializerMethodField()
    credit_request = serializers.SerializerMethodField()

    def get_order_number(self, obj):
        try:
            return obj.order.number
        except:
            return None

    def get_credit_request(self, obj):
        try:
            return obj.credit_request.credit_request_id
        except Exception as e:
            logger.error("error in credit req", exc_info=True)
            return None

    class Meta:
        model = CreditHistory
        fields = "__all__"  # Include all relevant fields


class CreditSerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()
    total_amount_added = serializers.SerializerMethodField()
    total_amount_radeemed = serializers.SerializerMethodField()

    class Meta:
        model = Credit
        fields = [
            "id",
            "user",
            "amount",
            "credit_gst",
            "credit_shipping_type",
            "total_amount_added",
            "total_amount_radeemed",
            "history",
        ]

    def get_total_amount_added(self, obj):
        return obj.remove_none(obj.total_amount_added)

    def get_total_amount_radeemed(self, obj):
        return obj.remove_none(obj.total_amount_radeemed)

    def get_history(self, obj):
        history = obj.history.all().order_by(
            "-credit_used_time"
        )  # Replace 'date_field' with your actual date field
        return CreditHistorySerializer(history, many=True).data
