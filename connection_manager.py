import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    # NOTE: This manager currently tracks ALL connections globally, which is
    # correct only while the server supports a single game session. Once rooms
    # are introduced, broadcast scope must move to a per-room group, not all
    # connections — this class will need to be instantiated once per room at
    # that point, not shared globally.

    def __init__(self) -> None:
        self._clients: set = set()

    async def register(self, websocket) -> None:
        self._clients.add(websocket)
        logger.info("Client connected: %s. Total clients: %d", websocket.remote_address, len(self._clients))

    async def unregister(self, websocket) -> None:
        self._clients.discard(websocket)
        logger.info("Client disconnected: %s. Total clients: %d", websocket.remote_address, len(self._clients))

    async def broadcast(self, message: dict) -> None:
        payload = json.dumps(message)
        for client in set(self._clients):
            try:
                await client.send(payload)
            except Exception as exc:
                logger.warning("Failed to send to client %s: %s", client.remote_address, exc)

    async def send_to(self, websocket, message: dict) -> None:
        await websocket.send(json.dumps(message))
