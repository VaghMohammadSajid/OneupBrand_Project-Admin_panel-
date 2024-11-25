from oscar.core.loading import get_model
from rest_framework import serializers

Voucher = get_model("voucher", "Voucher")


class VoucherRemoveSerializer(serializers.Serializer):
    vouchercode = serializers.CharField(max_length=128, required=True)

    def validate(self, attrs):
        # oscar expects this always to be uppercase.
        attrs["vouchercode"] = attrs["vouchercode"].upper()

        request = self.context.get("request")
        try:
            voucher = Voucher.objects.get(code=attrs.get("vouchercode"))

            # check expiry date
            # if not voucher.is_active():
            #     message = _("The '%(code)s' voucher has expired") % {
            #         "code": voucher.code
            #     }
            #     raise serializers.ValidationError(message)

            # check voucher rules
        #     is_available, message = voucher.is_available_to_user(request.user)
        #     if not is_available:
        #         raise serializers.ValidationError(message)
        except Voucher.DoesNotExist:
            raise serializers.ValidationError("Voucher Doesn't exist")

        # set instance to the voucher so we can use this in the view
        self.instance = voucher
        return attrs
