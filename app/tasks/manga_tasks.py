import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from celery import shared_task
from app.tasks.base import BaseTask
from app.core.redis_client import update_task_progress

logger = logging.getLogger(__name__)

@shared_task(bind=True, base=BaseTask, name="manga.process_batch")
def process_batch_task(self, items: list[dict]):
    task_id = self.request.id
    total = len(items)
    update_task_progress(task_id, {"status": "processing", "progress": 0, "total": total, "current": "init"})

    for i, item in enumerate(items):
        try:
            # 🔁 Llamada resiliente con tenacity (backoff exponencial)
            self._process_item_resilient(item)
            progress = int(((i + 1) / total) * 100)
            update_task_progress(task_id, {"progress": progress, "current": item.get("name", "unknown")})
        except Exception as e:
            logger.error(f"⚠️ Fallo en item {item.get('name')}: {e}")
            # Decidir si continuar o fallar la tarea completa

    return {"task_id": task_id, "processed": total}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)),
    reraise=True
)
def _process_item_resilient(self, item: dict):
    """Simula operación pesada con reintentos automáticos."""
    time.sleep(0.2)  # Reemplazar por pyvips/IO real
    # raise ConnectionError("Simulado para demo")