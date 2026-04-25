import redis
import redis.asyncio as aioredis
from app.config import settings

# Sync para Celery tasks (no bloquean event loop en workers)
redis_sync = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Async para FastAPI SSE (no bloquea request loop)
def get_async_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)

def update_task_progress(task_id: str, progress: dict):
    """Actualiza progreso en Redis hash + notifica vía pub/sub."""
    key = f"task:{task_id}"
    redis_sync.hset(key, mapping={k: str(v) for k, v in progress.items()})
    redis_sync.expire(key, 3600)  # TTL 1h para limpieza automática
    redis_sync.publish("task:progress", task_id)  # Despierta SSE subscribers