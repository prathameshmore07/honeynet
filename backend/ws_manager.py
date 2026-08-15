"""
HoneyNet WebSocket Connection Manager
Handles real-time streaming of telemetry, command events, risk alerts, and asset deployments.
"""
import json
import logging
import asyncio
from typing import List, Set, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("honeynet.ws")

class ConnectionManager:
    """Manages active WebSocket client connections for real-time SOC streaming."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON message to all connected clients asynchronously."""
        if not self.active_connections:
            return

        dead_connections = set()
        text_data = json.dumps(message)

        for connection in self.active_connections:
            try:
                await connection.send_text(text_data)
            except Exception:
                dead_connections.add(connection)

        for dead in dead_connections:
            self.active_connections.discard(dead)

# Global singleton
ws_manager = ConnectionManager()

# Thread-safe event loop dispatcher for background threads
_main_loop = None

def set_main_event_loop(loop):
    global _main_loop
    _main_loop = loop

def broadcast_sync(message: Dict[str, Any]):
    """Thread-safe synchronous wrapper to broadcast from background threads."""
    global _main_loop
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(message), _main_loop)
