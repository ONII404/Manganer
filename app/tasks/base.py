from celery import Task
from app.core.celery_app import celery_app
from app.core.redis_client import update_task_progress

class BaseTask(Task):
    """Base para todas las tareas con tracking y retry automático."""
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        update_task_progress(task_id, {"status": "failed", "error": str(exc), "progress": 100})
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        update_task_progress(task_id, {"status": "completed", "progress": 100})
        super().on_success(retval, task_id, args, kwargs)