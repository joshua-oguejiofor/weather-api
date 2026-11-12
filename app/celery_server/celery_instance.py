from celery import Celery
from app.core.config import settings


celery_app= Celery(
    broker= settings.REDIS_URL,
    backend= settings.REDIS_URL,
    include= ["app.celery_server.celery_tasks"]
)


celery_app.conf.update(
    task_serializer= "json",
    result_serializer= "json",
    accept_content= ["json"],
    timezone= "UTC",
    enable_utc= True,
)


