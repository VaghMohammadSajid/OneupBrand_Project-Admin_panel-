from django.shortcuts import render
from useraccount.models import ClientDetails
from .models import (
    Wallet,
    grand_total_added_to_client,
    grand_total_amount_radeemed_by_cliend,
)
from django.shortcuts import HttpResponse, render
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializer import WalletSerializer
from rest_framework import status

logger = logging.getLogger(__name__)


# Create your views here.
def total_amount(request):
    wallet = Wallet.objects.all()

    grand_total_added = grand_total_added_to_client().get("total_amount")
    grand_total_deducted = grand_total_amount_radeemed_by_cliend().get("total_amount")
    return render(
        request,
        "wallet/wallet_list.html",
        {
            "wallet": wallet,
            "grand_total_added": grand_total_added,
            "grand_total_deducted": grand_total_deducted,
            "page_data": "Wallet",
            "redirect_string": "wallet",
        },
    )


def wallet_history(request, id):

    wallet = Wallet.objects.get(id=id)

    all_history = wallet.history.all()
    radeemed_total = wallet.remove_none(wallet.total_amount_radeemed)
    added_total = wallet.remove_none(wallet.total_amount_added)
    return render(
        request,
        "wallet/wallet_history.html",
        {
            "history": all_history,
            "radeemed_total": radeemed_total,
            "added_total": added_total,
            "page_data": "Wallet",
        },
    )


class WalletHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        wallet = Wallet.objects.get(user=user)
        data = WalletSerializer(wallet).data
        logger.debug(data)
        return Response(data, status=status.HTTP_200_OK)


class WalletTotoalAmountAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            wallet = Wallet.objects.get(user=user)
            return Response({"amount": wallet.amount}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Wallet not found for this user"},
                status=status.HTTP_400_BAD_REQUEST,
            )
