from django.shortcuts import render
from rest_framework.views import APIView

# Create your views here.
import requests
import json
from rest_framework.response import Response


headers = {
    "Content-Type": "application/json",
    "account-id": f"a6477bbd82b9/4735e7a8-c7e3-4092-870c-d6cab932ce73",
    "api-key": "08a24107-847a-4bf5-bc0e-e892fb2b36dd",
}


class GstVerify(APIView):

    def post(self, request):
        data = request.data.get("gst_no")
        url_1 = (
            "https://eve.idfy.com/v3/tasks/async/verify_with_source/ind_gst_certificate"
        )

        payload = json.dumps(
            {
                "task_id": "74f4c926-250c-43ca-9c53-453e87ceacd1",
                "group_id": "8e16424a-58fc-4ba4-ab20-5bc8e7c3c41e",
                "data": {"gstin": f"{data}", "filing_status": True},
            }
        )

        response = requests.request("POST", url_1, headers=headers, data=payload)

        response_data = response.json()

        return Response({"req_id": response_data.get("request_id")})


class FinalCall(APIView):
    def post(self, request):
        response_data = request.data
        url_2 = f"https://eve.idfy.com/v3/tasks?request_id={response_data.get('request_id')}"

        payload = {}

        response = requests.request("GET", url_2, headers=headers, data=payload)

        return Response(response.json())