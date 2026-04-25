from celery import Celery
from app.config import settings

celery_app = Celery(
    "manganer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,          # ✅ Recuperación tras reinicio de worker
    worker_prefetch_multiplier=1, # ✅ Procesamiento justo, no acaparamiento
    broker_connection_retry_on_startup=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    worker_max_tasks_per_child=1000, # Evita memory leaks en workers long-running
)