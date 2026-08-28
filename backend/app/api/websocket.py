from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import connection_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/stations/{station_id}")
async def websocket_endpoint(websocket: WebSocket, station_id: str):
    await connection_manager.connect(websocket, station_id)
    try:
        while True:
            # Keep socket alive and receive client heartbeats/messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, station_id)
