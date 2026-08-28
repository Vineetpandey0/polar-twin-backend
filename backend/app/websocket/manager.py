import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger("websocket_manager")


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {
            "maitri": [],
            "bharati": [],
        }

    async def connect(self, websocket: WebSocket, station_id: str) -> None:
        await websocket.accept()
        st_id = station_id.lower()
        if st_id not in self.active_connections:
            self.active_connections[st_id] = []
        self.active_connections[st_id].append(websocket)
        logger.info(f"WebSocket connected for station '{st_id}'")

    def disconnect(self, websocket: WebSocket, station_id: str) -> None:
        st_id = station_id.lower()
        if st_id in self.active_connections and websocket in self.active_connections[st_id]:
            self.active_connections[st_id].remove(websocket)
            logger.info(f"WebSocket disconnected for station '{st_id}'")

    async def broadcast(self, station_id: str, message: dict) -> None:
        st_id = station_id.lower()
        if st_id not in self.active_connections:
            return
        dead = []
        for connection in self.active_connections[st_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending websocket message: {e}")
                dead.append(connection)
        for d in dead:
            self.disconnect(d, st_id)


connection_manager = ConnectionManager()
