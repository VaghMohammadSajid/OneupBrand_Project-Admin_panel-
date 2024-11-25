from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import base64
import os
from oneup_project import settings


def send_order_confirmation_email(order, total_offer_):

    try:

        order_lines = order.basket.lines.all()
        print(order.__dict__)
        subject = "Order Confirmation"
        STATIC_ROOT = os.path.join(settings.BASE_DIR, "static/")
        image_path = os.path.join(STATIC_ROOT, "oscar/email_img/img", "log.png")
        product_image_urls = []
        for single_order in order_lines:
            single_images = single_order.product.images.all()[0]
            print(single_images.original)
            product_image_urls.append(single_images.original)

        total_list = zip(order_lines, product_image_urls)
        sub_total = order.total_incl_tax + total_offer_ - order.shipping_incl_tax

        message = render_to_string(
            "email/email.html",
            {
                "order": order,
                "shipping_addres": order.shipping_address,
                "lines": order_lines,
                "total_offer": total_offer_,
                "images": product_image_urls,
                "full": total_list,
                "sub": sub_total,
            },
        )

        sender = settings.ORDER_HOST
        email = EmailMultiAlternatives(
            subject, from_email=sender, to=[order.shipping_address.email]
        )
        email.attach_alternative(message, "text/html")
        email.send()
    except Exception as e:
        sender = settings.EMAIL_HOST_USER
        send_mail(
            subject,
            str(e),
            sender,
            ["pranavpranab@gmail.com"],
        )
