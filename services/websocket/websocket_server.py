from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import List
import json
import logging
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Connection closed. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo received messages back to all clients
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/notify")
async def notify_clients(data: dict):
    try:
        message = json.dumps(data)
        await manager.broadcast(message)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in notify_clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = 8765
    
    logger.info("Starting WebSocket server...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        exit(1)
