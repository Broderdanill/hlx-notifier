
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Dict, List
import uvicorn
import secrets
import os
import logging
from urllib.parse import unquote

# Initiera logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()
security = HTTPBasic()

channels: Dict[str, List[WebSocket]] = {}

# Läs användare/lösen från miljövariabler (standard fallback)
VALID_USERNAME = os.getenv("AUTH_USERNAME", "admin")
VALID_PASSWORD = os.getenv("AUTH_PASSWORD", "supersecret")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, VALID_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, VALID_PASSWORD)
    if not (correct_username and correct_password):
        logger.warning("Felaktiga autentiseringsuppgifter: %s", credentials.username)
        raise HTTPException(status_code=401, detail="Unauthorized")
    logger.debug("Autentisering lyckades för användare: %s", credentials.username)

@app.post("/notify")
async def notify(request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    data = await request.json()
    channel = data.get("channel")
    message = data.get("message")

    logger.info("Mottog notis: kanal=%s, meddelande=%s", channel, message)

    if not channel or not message:
        logger.warning("Ogiltig notis – saknar kanal eller meddelande")
        return {"error": "Missing channel or message"}

    connections = channels.get(channel, [])
    logger.debug("Hittade %d klienter för kanal %s", len(connections), channel)
    for ws in connections:
        await ws.send_json({"channel": channel, "message": message})
        logger.debug("Skickade meddelande till WebSocket för kanal %s", channel)

    return {"status": "Notification sent", "clients": len(connections)}

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    channel = unquote(channel)
    await websocket.accept()

    if channel not in channels:
        channels[channel] = []
    channels[channel].append(websocket)
    logger.info("Ny WebSocket anslutning till kanal: %s", channel)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        channels[channel].remove(websocket)
        logger.info("WebSocket frånkopplad från kanal: %s", channel)

if __name__ == "__main__":
    logger.info("Startar notifieringsserver på port 3083...")
    uvicorn.run(app, host="0.0.0.0", port=3083)