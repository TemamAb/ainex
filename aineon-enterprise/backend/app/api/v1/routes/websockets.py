from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # In a real application, you would get data from a source
            # and broadcast it. For now, we'll just send a message
            # every 5 seconds.
            await asyncio.sleep(5)
            await manager.broadcast("Real-time update: System is running.")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A client has disconnected.")
