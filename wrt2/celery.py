# myproject/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from wrt2.settings import broker_url, result_backend

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wrt2.settings")

app = Celery(
    "wrt2",
    redis_max_connections=1,
    broker_transport_options={"max_connections": 1},
    broker_pool_limit=1,
)

# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.update(
    broker_url=broker_url,
    result_backend=result_backend,
    broker_transport_options={"max_connections": 1},
    result_backend_transport_options={"max_connections": 2},
    redis_max_connections=2,
    worker_concurrency=1,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # task_ignore_result=True,
    task_store_errors_even_if_ignored=False,
    task_track_started=False,
    worker_send_task_events=False,
    task_send_sent_event=False,
    worker_disable_rate_limits=True,
    worker_max_tasks_per_child=1,
    broker_pool_limit=1,
    broker_heartbeat=None,
    result_expires=3600,
)

# Ensure Celery can discover tasks from all apps
app.autodiscover_tasks()
