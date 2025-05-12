from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Tuple
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.websockets import WebSocketState
import uvicorn
import asyncio
import logging
from urllib.parse import unquote, parse_qs

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# App och rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_middleware(BaseHTTPMiddleware, dispatch=limiter.middleware)

# WebSocket-kanaler
channels: Dict[str, List[Tuple[WebSocket, str]]] = {}
push_counter = 0

# Input-modell
class NotificationPayload(BaseModel):
    channel: str
    message: str
    originClientId: str | None = None

@app.post("/notify")
@limiter.limit("5/second")
async def notify(payload: NotificationPayload, request: Request):
    global push_counter
    channel = payload.channel
    message = payload.message
    origin_client_id = payload.originClientId

    if not channel or not message:
        raise HTTPException(status_code=400, detail="Missing channel or message")

    connections = channels.get(channel, [])
    sent = 0
    for ws, client_id in connections:
        if origin_client_id and client_id == origin_client_id:
            continue
        try:
            await ws.send_json({"channel": channel, "message": message})
            sent += 1
        except Exception as e:
            logger.error("Failed to send to %s: %s", client_id, e)

    logger.info("Push to channel=%s, sent=%d", channel, sent)
    push_counter += sent
    return {"status": "ok", "sent": sent}

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    channel = unquote(channel)
    query_params = parse_qs(websocket.scope["query_string"].decode())
    client_id = query_params.get("clientId", ["unknown"])[0]

    await websocket.accept()

    if channel not in channels:
        channels[channel] = []

    # Ta bort tidigare anslutningar med samma clientId
    channels[channel] = [(ws, cid) for ws, cid in channels[channel] if cid != client_id]

    channels[channel].append((websocket, client_id))
    logger.info("New WebSocket: channel=%s, clientId=%s", channel, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            if data.strip().lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        channels[channel] = [(ws, cid) for ws, cid in channels[channel] if ws != websocket]
        logger.info("Disconnected: channel=%s, clientId=%s", channel, client_id)

@app.get("/status")
async def status():
    return {
        "channels": {ch: len(clients) for ch, clients in channels.items()},
        "total_pushes": push_counter
    }

@app.on_event("startup")
async def cleanup_dead_sockets():
    async def cleaner():
        while True:
            for channel, connections in list(channels.items()):
                live = []
                for ws, client_id in connections:
                    if ws.client_state != WebSocketState.CONNECTED:
                        logger.info("Removing dead socket: %s", client_id)
                    else:
                        live.append((ws, client_id))
                channels[channel] = live
            await asyncio.sleep(30)
    asyncio.create_task(cleaner())

if __name__ == "__main__":
    uvicorn.run("main_hardened:app", host="0.0.0.0", port=3083)