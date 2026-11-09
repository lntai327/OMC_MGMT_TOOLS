import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.ws_manager import ws_manager

logger = logging.getLogger("ws_job_progress")
router = APIRouter(prefix="/ws", tags=["WebSockets"])


@router.websocket("/jobs/{job_id}")
async def websocket_job_progress(websocket: WebSocket, job_id: str):
    await ws_manager.connect(websocket, job_id)
    redis_conn = aioredis.from_url(settings.REDIS_URL)
    pubsub = redis_conn.pubsub()
    await pubsub.subscribe(f"job:{job_id}")

    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Error in Redis listener: {e}")

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            # Keep connection alive and accept client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from WebSocket job {job_id}")
    finally:
        listener_task.cancel()
        await pubsub.unsubscribe(f"job:{job_id}")
        await redis_conn.close()
        ws_manager.disconnect(websocket, job_id)

