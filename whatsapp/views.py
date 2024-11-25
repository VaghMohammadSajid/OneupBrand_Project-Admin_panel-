from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
import requests

# Create your views here.


class SendMessage:
    def send_whatsapp_message(self, **data):
        name = data.get("name")
        order_id = data.get("order_id")
        mobile_no = data.get("mobile_no")

        HEADERS = {
            "Authorization": "Bearer EAAWXK3o6HMEBO6S1yVeik0gyeDyjZBNl2MvcQmz83kSc27BmcviLAm2ffnlEGCA7DdhDwzN84AYtZA5mhzZAVlQUIPkiFMbisyy1TzZBR5w1U1bpJhmeJnfLZAfkvRHiQUwe3ZAJMfc8hCR2QZALCmyY7xDNxCZAHN3hnxEmdtzfON9irKHtf0zXBfh8h3093zdbxT7YKqfgh9tlZApgMjVvKOPssQHQxupHRMYppSYIZD",
            "Content-Type": "application/json",
        }

        body = {
            "messaging_product": "whatsapp",
            "to": f"{mobile_no}",
            "type": "template",
            "template": {
                "name": "order",
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "BODY",
                        "parameters": [
                            {"type": "text", "text": f"{name}"},
                            {"type": "text", "text": f"{order_id}"},
                        ],
                    },
                ],
            },
        }
        res = requests.post(
            url="https://graph.facebook.com/v19.0/387436267781727/messages",
            json=body,
            headers=HEADERS,
        )
