from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import logging
from celery.signals import setup_logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oneup_project.settings")

app = Celery("oneup_project")

# Using a string here means the worker does not have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")


# Load task modules from all registered Django app configs.
@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig  # noqa
    from django.conf import settings  # noqa

    dictConfig(settings.LOGGING)


app.autodiscover_tasks()
# Adjust as needed


@app.task(bind=True)
def debug_task():
    print(f"Request: {self.request!r}")
