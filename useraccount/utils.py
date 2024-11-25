from oscar.apps.voucher.models import Voucher
from datetime import date
from django.core.mail import send_mail
from oneup_project.settings import EMAIL_HOST_USER
import requests
from oneup_project.settings import ERP_URL,ERP_TOKEN


def check_voucher_code(data):
    today = date.today()

    try:
        voucher_details = Voucher.objects.get(
            code=data, start_datetime__lte=today, end_datetime__gte=today
        )
    except Voucher.DoesNotExist:
        return True, "no code found"
    if not voucher_details.num_orders == 0:
        return True, "voucher already used"
    return False, voucher_details


def send_client_data_to_user(data):
    url = f"{ERP_URL}api/method/django_ecommerce.api.update_customer"

    headers = {
        "Authorization": f"token {ERP_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Error sending client data: {e}")


def create_unique_string_for_all_users():

    from django.contrib.auth.models import User

    for i in User.objects.all():
        generate_unique_string(i)


def generate_unique_string(i):
    from datetime import datetime
    from .models import UniqueStrings
    from django.db.models import Max

    current_year = datetime.now().year
    prefix = "OUB" + str(current_year)
    existing_strings = UniqueStrings.objects.filter(unique_string__startswith=prefix)
    new_unique_string = UniqueStrings.objects.create(user=i)
    if existing_strings.exists():

        last_string = existing_strings.aggregate(max_digit=Max("digit"))["max_digit"]
        new_string = prefix + str(last_string + 1)
        new_unique_string.digit = int(last_string + 1)
    else:

        new_string = prefix + "1"
        new_unique_string.digit = 1
    new_unique_string.unique_string = new_string
    new_unique_string.save()
