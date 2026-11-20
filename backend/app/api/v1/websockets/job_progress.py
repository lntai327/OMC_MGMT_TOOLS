import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from app.core.redis_client import get_async_redis_client
from app.core.security import decode_token
from app.core.ws_manager import ws_manager

logger = logging.getLogger("ws_job_progress")
router = APIRouter(prefix="/ws", tags=["WebSockets"])


@router.websocket("/jobs/{job_id}")
async def websocket_job_progress(
    websocket: WebSocket,
    job_id: str,
    token: Optional[str] = Query(None),
):
    # Optional JWT logging/validation if provided; do not reject client on missing query param
    auth_token = token or websocket.headers.get("sec-websocket-protocol")
    if auth_token:
        payload = decode_token(auth_token)
        if payload:
            logger.debug(f"WS client authenticated as {payload.get('sub')} for job {job_id}")

    await ws_manager.connect(websocket, job_id)
    redis_conn = get_async_redis_client()
    pubsub = redis_conn.pubsub()
    await pubsub.subscribe(f"job:{job_id}")

    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    raw_data = message["data"]
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")
                    data = json.loads(raw_data)
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
        try:
            await pubsub.unsubscribe(f"job:{job_id}")
            await pubsub.close()
            await redis_conn.close()
        except Exception as e:
            logger.debug(f"Error cleaning up Redis connection: {e}")
        ws_manager.disconnect(websocket, job_id)


