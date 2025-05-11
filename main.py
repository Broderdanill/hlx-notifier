from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Dict, List, Tuple
import uvicorn
import secrets
import os
import logging
from urllib.parse import unquote, parse_qs

# Initialize logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
security = HTTPBasic()

# Dictionary mapping channels to list of (WebSocket, clientId)
channels: Dict[str, List[Tuple[WebSocket, str]]] = {}

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
    origin_client_id = data.get("originClientId")  # Optional

    logger.info("Received notification: channel=%s, message=%s, originClientId=%s",
                channel, message, origin_client_id)

    if not channel or not message:
        logger.warning("Invalid notification – missing channel or message")
        return {"error": "Missing channel or message"}

    connections = channels.get(channel, [])
    sent = 0
    for ws, client_id in connections:
        if origin_client_id and origin_client_id == client_id:
            logger.debug("Skipping sender clientId=%s", client_id)
            continue
        try:
            await ws.send_json({"channel": channel, "message": message})
            logger.debug("Sent message to clientId=%s on channel=%s", client_id, channel)
            sent += 1
        except Exception as e:
            logger.error("Failed to send to clientId=%s: %s", client_id, e)

    return {"status": "Notification sent", "clients": sent}

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    channel = unquote(channel)
    query_params = parse_qs(websocket.scope["query_string"].decode())
    client_id = query_params.get("clientId", ["unknown"])[0]

    await websocket.accept()

    if channel not in channels:
        channels[channel] = []
    channels[channel].append((websocket, client_id))
    logger.info("New WebSocket connection on channel: %s (clientId=%s)", channel, client_id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        channels[channel] = [
            (ws, cid) for ws, cid in channels[channel] if ws != websocket
        ]
        logger.info("WebSocket disconnected from channel: %s (clientId=%s)", channel, client_id)

if __name__ == "__main__":
    logger.info("Starting notification server on port 3083...")
    uvicorn.run(app, host="0.0.0.0", port=3083)
