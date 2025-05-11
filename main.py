
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Dict, List
import uvicorn
import secrets
import os

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
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.post("/notify")
async def notify(request: Request, credentials: HTTPBasicCredentials = Depends(authenticate)):
    data = await request.json()
    channel = data.get("channel")
    message = data.get("message")

    if not channel or not message:
        return {"error": "Missing channel or message"}

    connections = channels.get(channel, [])
    for ws in connections:
        await ws.send_json({"channel": channel, "message": message})

    return {"status": "Notification sent", "clients": len(connections)}

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await websocket.accept()
    if channel not in channels:
        channels[channel] = []
    channels[channel].append(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        channels[channel].remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
