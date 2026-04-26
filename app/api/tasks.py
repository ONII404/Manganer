# app/api/tasks.py
import json
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from redis.asyncio import ConnectionError as RedisConnError
from app.tasks.manga_tasks import process_batch_task
from app.core.redis_client import get_async_redis
import logging

# ✅ tags definido aquí, NO en include_router() de main.py
router = APIRouter(tags=["Tasks"])
logger = logging.getLogger(__name__)

class TaskSubmitRequest(BaseModel):
    items: list[dict]

# ✅ Ruta: POST /api/v1/tasks/submit
@router.post("/submit")
def submit_task(req: TaskSubmitRequest):
    task = process_batch_task.delay(req.items)
    return {"task_id": task.id, "status": "queued"}

# ✅ Ruta: GET /api/v1/tasks/stream/{task_id}
@router.get("/stream/{task_id}")
async def stream_task(task_id: str):
    async def event_stream():
        r = get_async_redis()
        try:
            state = await r.hgetall(f"task:{task_id}")
            if not state:
                yield f"data: {json.dumps({'status': 'not_found'})}\n\n"
                return
            yield f"data: {json.dumps(state)}\n\n"

            pubsub = r.pubsub()
            await pubsub.subscribe("task:progress")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    state = await r.hgetall(f"task:{task_id}")
                    if state:
                        yield f"data: {json.dumps(state)}\n\n"
                    if state.get("status") in ("completed", "failed"):
                        yield f"data: {json.dumps({'status': 'finished', **state})}\n\n"
                        break
        except RedisConnError as e:
            logger.error(f"🔌 Error conexión Redis SSE: {e}")
            yield f"data: {json.dumps({'status': 'error', 'detail': 'Redis connection lost'})}\n\n"
        finally:
            if 'pubsub' in locals():
                await pubsub.unsubscribe("task:progress")
                await pubsub.close()
            await r.close()

    return StreamingResponse(event_stream(), media_type="text/event-stream")