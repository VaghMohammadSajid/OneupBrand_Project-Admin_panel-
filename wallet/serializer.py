from rest_framework import serializers
from .models import Wallet, WalletHistory


class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletHistory
        fields = "__all__"


class WalletSerializer(serializers.ModelSerializer):
    history = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ["id", "amount", "history"]

    def get_history(self, obj):
        return HistorySerializer(obj.history.all(), many=True).data
