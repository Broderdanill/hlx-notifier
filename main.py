from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Dict, List
import uvicorn
import secrets
import os
import logging
from urllib.parse import unquote

# Initialize logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
security = HTTPBasic()

# Dictionary mapping channels to lists of connected WebSockets
channels: Dict[str, List[WebSocket]] = {}

# Read username/password from environment variables (default fallback)
VALID_USERNAME = os.getenv("AUTH_USERNAME", "admin")
VALID_PASSWORD = os.getenv("AUTH_PASSWORD", "supersecret")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, VALID_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, VALID_PASSWORD)
    if not (correct_username and correct_password):
        logger.warning("Invalid authentication attempt: %s", credentials.username)
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.debug("Authentication succeeded for user: %s", credentials.username)

@app.post("/notify")
async def notify(request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    data = await request.json()
    channel = data.get("channel")
    message = data.get("message")

    logger.info("Received notification: channel=%s, message=%s", channel, message)

    if not channel or not message:
        logger.warning("Invalid notification – missing channel or message")
        return {"error": "Missing channel or message"}

    connections = channels.get(channel, [])
    logger.debug("Found %d clients for channel %s", len(connections), channel)
    for ws in connections:
        await ws.send_json({"channel": channel, "message": message})
        logger.debug("Sent message to WebSocket for channel %s", channel)

    return {"status": "Notification sent", "clients": len(connections)}

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    channel = unquote(channel)
    await websocket.accept()

    if channel not in channels:
        channels[channel] = []
    channels[channel].append(websocket)
    logger.info("New WebSocket connection on channel: %s", channel)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        channels[channel].remove(websocket)
        logger.info("WebSocket disconnected from channel: %s", channel)

if __name__ == "__main__":
    logger.info("Starting notification server on port 3083...")
    uvicorn.run(app, host="0.0.0.0", port=3083)
