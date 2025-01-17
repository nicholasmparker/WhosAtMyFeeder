from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import List, Dict
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_count = 0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(f"New connection. Total connections: {self.connection_count}")
        # Send initial connection status
        await self.broadcast_status()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        self.connection_count -= 1
        logger.info(f"Connection closed. Total connections: {self.connection_count}")

    async def broadcast_status(self):
        """Broadcast connection status to all clients"""
        if not self.active_connections:
            return
        
        status_message = {
            "type": "status",
            "data": {
                "connections": self.connection_count,
                "status": "connected"
            }
        }
        await self.broadcast(status_message)

    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

    async def broadcast_detection(self, detection_data: Dict):
        """Broadcast a new bird detection to all clients"""
        message = {
            "type": "detection",
            "data": detection_data
        }
        await self.broadcast(message)

manager = ConnectionManager()

@app.post("/notify")
async def notify_detection(request: Request):
    """Receive detection notifications from the main application"""
    try:
        detection_data = await request.json()
        await manager.broadcast_detection(detection_data)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error handling notification: {e}")
        return {"status": "error", "message": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            data = await websocket.receive_text()
            # Handle any incoming messages if needed
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast_status()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
        await manager.broadcast_status()

# Function to be called from the main application when a new detection occurs
async def handle_new_detection(detection_data: Dict):
    """Handle new bird detection and broadcast to all clients"""
    await manager.broadcast_detection(detection_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
