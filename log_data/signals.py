# # logs/signals.py
# from django.db.models.signals import post_save, post_delete, pre_save
# from django.dispatch import receiver
# from .models import ActionLog
# from django.contrib.auth.models import User
# from django.forms.models import model_to_dict
# from role_permission.middleware import get_current_request
# import json
# import logging
# import json
# from datetime import datetime, date
# from decimal import Decimal
# from uuid import UUID
# from collections.abc import Iterable


# logger = logging.getLogger(__name__)

# def log_action(user, action, instance, changes=None):
#     if not changes == None:
#         pass
#         # logger.debug(changes)
#     # logger.debug(user)
#     try:
#         ActionLog.objects.create(
#             user=user,
#             action=action,
#             model_name=instance.__class__.__name__,
#             object_id=instance.pk,
#             changes=changes
#         )
#     except Exception as e:
#         # logger.debug(user)
#         # try:
#         #     logger.debug(user.is_authenticated)
#         # except:
#             pass
# def custom_serializer(obj):
#     if isinstance(obj, (datetime, date)):
#         return obj.isoformat()
#     elif isinstance(obj, Decimal):
#         return float(obj)
#     elif isinstance(obj, UUID):
#         return str(obj)
#     elif isinstance(obj, set) or isinstance(obj, frozenset):
#         return list(obj)
#     elif isinstance(obj, bytes):
#         return obj.decode('utf-8')
#     elif isinstance(obj, complex):
#         return {'real': obj.real, 'imag': obj.imag}
#     elif isinstance(obj, Iterable):
#         return list(obj)
#     raise TypeError(f"Type {type(obj)} not serializable")

# @receiver(pre_save)
# def log_update_changes(sender, instance, **kwargs):
#     logger.debug(f"{sender=}")
#     if sender == ActionLog:  # Avoid logging the logging model itself
#         return
#     try:
#         old_instance = sender.objects.get(pk=instance.pk)
#     except sender.DoesNotExist:
#         # Object is new, so this is a create action
#         old_instance = None

#     request = get_current_request()
#     user = request.user if request else None
#     logger.debug(old_instance)
#     logger.debug("called multiple times")
#     if old_instance and user:
#         logger.debug("inside if")
#         changes = {}
#         for field in instance._meta.fields:
#             field_name = field.name
#             old_value = getattr(old_instance, field_name)
#             new_value = getattr(instance, field_name)
#             if old_value != new_value:
#                 changes[field_name] = {'old': old_value, 'new': new_value}

#         changes = json.dumps(changes, default=custom_serializer, indent=4)

#         log_action(user, 'UPDATE', instance, changes)

# @receiver(post_save)
# def log_create(sender, instance, created, **kwargs):
#     logger.debug(f"{sender=}")
#     if type(sender) == type(ActionLog):
#         return

#     request = get_current_request()
#     user = request.user if request else None

#     if created and user:
#         log_action(user, 'CREATE', instance)

# @receiver(post_delete)
# def log_delete(sender, instance, **kwargs):
#     logger.debug(f"{sender=} {ActionLog}")
#     if sender == ActionLog:
#         return


#     request = get_current_request()
#     user = request.user if request else None

#     if user:
#         log_action(user, 'DELETE', instance)
