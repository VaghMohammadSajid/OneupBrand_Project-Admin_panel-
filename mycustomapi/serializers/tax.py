# import serializer from rest_framework
from rest_framework import serializers

from mycustomapi.models import *


# create a serializer
class GSTGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTGroup
        fields = ["id", "gst_group_code", "description", "rate"]


class GSTSetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSTSetup
        fields = [
            "id",
            "hsn_code",
            "hsn_description",
            "gst_rate",
            "sgst_rate",
            "cgst_rate",
            "igst_rate",
        ]
