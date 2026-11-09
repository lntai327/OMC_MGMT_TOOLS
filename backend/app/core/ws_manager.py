import json
from typing import Dict, List
from fastapi import WebSocket
import logging

logger = logging.getLogger("ws_manager")


class WebSocketConnectionManager:
    """Manages active WebSocket connections grouped by job_id."""

    def __init__(self):
        # job_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket client connected to job {job_id}. Total: {len(self.active_connections[job_id])}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info(f"WebSocket client disconnected from job {job_id}")

    async def broadcast_job_progress(self, job_id: str, data: dict):
        if job_id in self.active_connections:
            dead_connections = []
            message = json.dumps(data)
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.warning(f"Error sending WS update: {e}")
                    dead_connections.append(connection)

            for dead in dead_connections:
                self.disconnect(dead, job_id)


ws_manager = WebSocketConnectionManager()

