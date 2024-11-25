from rest_framework import serializers
from .models import (
    ClientDetails,
    OTP,
    Contact,
    UserProfile,
    VoucherUser,
    ClientEmailVerify,
    OnboardingGstVerify,
    RequestBussinessRegister,
    OnboardingBussinessDetails,
    OnboardingBankDetails,
    # OnboardingAlternativePersonDetails,
    GetHelpOnHomePage,
    OnboardingCommunication,
    OnboardingRegisteredAddress,
    WarehouseAddress,
    OutletAddress

)
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["id", "username"]


class VoucherSerializer(serializers.Serializer):
    code = serializers.CharField()


class EmailSentSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    mobile_number = serializers.CharField()


class SignupCheckingSerializer(serializers.Serializer):
    email = serializers.EmailField()
    mobile_number = serializers.CharField()


class VarifyRegistrationSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    mobile_number = serializers.CharField()


class ClientDetailsSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ClientDetails
        fields = "__all__"

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()

        return super(ClientDetailsSerializer, self).update(instance, validated_data)


class VoucherUsertDetailsSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = VoucherUser
        fields = "__all__"

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()

        return super(VoucherUsertDetailsSerializer, self).update(
            instance, validated_data
        )


class PasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class VerifyOTPSerializer(serializers.Serializer):
    OTP = serializers.IntegerField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"


class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(default="-")
    last_name = serializers.CharField(default="-")
    date_of_birth = serializers.DateField(default="-")
    email = serializers.EmailField(default="-")
    gender = serializers.EmailField(default="-")

    class Meta:
        model = UserProfile
        fields = [
            "mobile_number",
            "first_name",
            "last_name",
            "date_of_birth",
            "email",
            "gender",
        ]


class ClientEmailVerifySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientEmailVerify
        fields = ["email", "otp"]


from rest_framework import serializers


class ChildStructureSerializer(serializers.Serializer):
    id = serializers.CharField()
    brand = serializers.CharField()
    image = serializers.ListField(child=serializers.URLField())
    price = serializers.FloatField()
    title = serializers.CharField()
    is_public = serializers.BooleanField()
    item_code = serializers.CharField()
    structure = serializers.CharField()
    Parent_UPC = serializers.CharField()
    attributes = serializers.ListField(child=serializers.DictField(), required=False)
    best_seller = serializers.BooleanField()
    description = serializers.CharField()
    num_in_stock = serializers.IntegerField()
    product_type = serializers.CharField()
    stock_record = serializers.DictField(required=False)
    Specification = serializers.CharField()
    standard_rate = serializers.FloatField()
    first_category = serializers.DictField()
    is_discountable = serializers.BooleanField()
    shipment_dimensions = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    recommended_products = serializers.ListField(
        child=serializers.CharField(), required=False
    )


class ParentSerializer(serializers.Serializer):
    id = serializers.CharField()
    brand = serializers.CharField()
    image = serializers.ListField(child=serializers.URLField())
    price = serializers.FloatField()
    title = serializers.CharField()
    hsn_code = serializers.CharField()
    is_public = serializers.BooleanField()
    item_code = serializers.CharField()
    structure = serializers.CharField()
    attributes = serializers.ListField(child=serializers.DictField(), required=False)
    best_seller = serializers.BooleanField()
    description = serializers.CharField()
    num_in_stock = serializers.IntegerField()
    product_type = serializers.CharField()
    stock_record = serializers.DictField(required=False)
    Specification = serializers.CharField()
    standard_rate = serializers.FloatField()
    first_category = serializers.DictField()
    child_structure = ChildStructureSerializer(many=True, required=False)
    is_discountable = serializers.BooleanField()
    shipment_dimensions = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    recommended_products = serializers.ListField(
        child=serializers.CharField(), required=False
    )


class ParentListSerializer(serializers.Serializer):
    data = ParentSerializer(many=True)


class OnboardingRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestBussinessRegister
        fields = "__all__"


class OnboardingGstSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingGstVerify
        fields = "__all__"


class OnboardingBussinessDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingBussinessDetails
        fields = "__all__"


# class OnboardingAlternativePersonDetailsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = OnboardingAlternativePersonDetails
#         fields = "__all__"


class OnboardingBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingBankDetails
        fields = "__all__"
        extra_kwargs = {
            "upload_pan": {"required": False, "allow_null": True},
            "upload_gst": {"required": False, "allow_null": True},
            "certificate_of_corporation": {"required": False, "allow_null": True},
            "msme": {"required": False, "allow_null": True},
            "authorization_letter": {"required": False, "allow_null": True},
            "aadhar": {"required": False, "allow_null": True},
        }


class GetHelpOnHomePageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = GetHelpOnHomePage
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "image",
            "message",
        ]


class OnboardingCommunictionSerializer(serializers.ModelSerializer):

    class Meta:
        model = OnboardingCommunication
        fields = "__all__"


class OnboardingregisterAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = OnboardingRegisteredAddress
        fields = "__all__"
class OnboardingWarehouseAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = WarehouseAddress
        fields = "__all__"
class OnboardingOutletAddresssSerializer(serializers.ModelSerializer):

    class Meta:
        model = OutletAddress
        fields = "__all__"

class FullDataSerializer(serializers.Serializer):
    bank = OnboardingBankDetailsSerializer()
