from celery import shared_task
import time
import requests
import logging
from useraccount.models import UpdateErpstatus
from oneup_project.settings import ERP_URL,ERP_TOKEN
from oneup_project import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)
ERP_URL = (
    f"{ERP_URL}api/method/django_ecommerce.api.update_item_status"
)
HEADERS = {
    "Authorization": f"token {ERP_TOKEN}",
    "Content-Type": "application/json",
}


@shared_task
def long_running_task(created_item_upc):

    try:
        sender = settings.EMAIL_HOST_USER

        send_mail(
                    "task runner failed for freeze",
                    str(f),
                    sender,
                    ["pranavpranab@gmail.com"],
                )
    except Exception as e:
         logger.error("error in sending product status",exc_info=True)

    for single_upc in created_item_upc:
        try:
            start_time = time.time()
            response = requests.post(
                url=ERP_URL, headers=HEADERS, json={"item_code": [single_upc]}
            )
            logger.debug(f"elapsed_time = {time.time() - start_time}")
            logger.debug(response.__dict__)
            status = UpdateErpstatus.objects.filter(upc=single_upc).update(
                update_erp=True
            )

        except Exception as e:
            import traceback

            f = traceback.format_exc()
            logger.debug(f"error in updating status in erp {f=}")


@shared_task
def task_testing():    
    logger.debug("celery working fine")