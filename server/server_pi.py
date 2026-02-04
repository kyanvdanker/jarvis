# server_pi.py  (or rename to main.py if preferred)
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from typing import Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = FastAPI(title="Jarvis Wearable Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory device manager (replace with Redis/DB later)
class DeviceManager:
    def __init__(self):
        self.command_sockets: Dict[str, WebSocket] = {}

    async def register_command_socket(self, device_id: str, ws: WebSocket):
        self.command_sockets[device_id] = ws

    async def unregister_command_socket(self, device_id: str):
        self.command_sockets.pop(device_id, None)

    async def send_command(self, device_id: str, payload: dict):
        ws = self.command_sockets.get(device_id)
        if ws:
            try:
                await ws.send_json(payload)
                logging.info(f"[cmd sent] to {device_id}: {payload.get('type')}")
            except Exception as e:
                logging.error(f"[cmd send fail] {device_id}: {e}")
                await self.unregister_command_socket(device_id)
        else:
            logging.warning(f"[cmd] {device_id} not connected")

devices = DeviceManager()

# Global flags (later move to DB or per-device state)
translation_enabled: Dict[str, bool] = {}  # per device

# ────────────────────────────────────────────────
# Audio WebSocket – receives raw audio chunks
# ────────────────────────────────────────────────
@app.websocket("/ws/audio")
async def ws_audio(websocket: WebSocket, device_id: str = Query(...)):
    await websocket.accept()
    logging.info(f"[audio] Device {device_id} connected")

    try:
        while True:
            data = await websocket.receive_bytes()
            # TODO: Here you process audio:
            # - feed to whisper / faster-whisper
            # - detect speech → send to LLM
            # - if translation_enabled.get(device_id, False): translate
            logging.debug(f"[audio chunk] {len(data)} bytes from {device_id}")
    except WebSocketDisconnect:
        logging.info(f"[audio] Device {device_id} disconnected")
    except Exception:
        logging.exception(f"[audio] Error for {device_id}")

# ────────────────────────────────────────────────
# Commands WebSocket – server pushes to device
# ────────────────────────────────────────────────
@app.websocket("/ws/commands")
async def ws_commands(websocket: WebSocket, device_id: str = Query(...)):
    await websocket.accept()
    await devices.register_command_socket(device_id, websocket)
    logging.info(f"[cmd] Device {device_id} connected")

    try:
        # Keep alive – client doesn't send much
        while True:
            await websocket.receive_text()  # or .receive() if binary
    except WebSocketDisconnect:
        logging.info(f"[cmd] Device {device_id} disconnected")
    except Exception:
        logging.exception(f"[cmd] Error for {device_id}")
    finally:
        await devices.unregister_command_socket(device_id)

# ────────────────────────────────────────────────
# Heartbeat
# ────────────────────────────────────────────────
class HeartbeatPayload(BaseModel):
    device_id: str
    uptime: float
    timestamp: float

@app.post("/api/heartbeat")
async def heartbeat(payload: HeartbeatPayload):
    logging.info(f"[hb] {payload.device_id} uptime={payload.uptime:.1f}s ts={payload.timestamp}")
    # Could update last_seen timestamp here
    return {"status": "ok"}

# ────────────────────────────────────────────────
# Control endpoint – called from phone Shortcuts
# ────────────────────────────────────────────────
@app.get("/control")  # or POST if you prefer body
async def control_pi(
    action: str = Query(...),
    value: str = Query(None),
    device_id: str = Query("kyan-glasses-01")  # default or require
):
    if action == "mute":
        state = value.lower() in ("on", "true", "1")
        await devices.send_command(device_id, {"type": "mute", "state": state})
        return {"status": "sent", "action": "mute", "state": state}

    elif action == "toggle_translation":
        enabled = value.lower() in ("on", "true", "1") if value else True
        translation_enabled[device_id] = enabled
        msg = f"Translation {'enabled' if enabled else 'disabled'}"
        await devices.send_command(device_id, {"type": "notify", "message": msg})
        return {"status": "sent", "action": "translation", "enabled": enabled}

    elif action == "status":
        connected = device_id in devices.command_sockets
        return {"connected": connected, "translation": translation_enabled.get(device_id, False)}

    return JSONResponse({"error": "unknown action"}, status_code=400)

# ────────────────────────────────────────────────
# Test TTS push
# ────────────────────────────────────────────────
class TTSCommand(BaseModel):
    device_id: str
    text: str

@app.post("/api/test/tts")
async def test_tts(cmd: TTSCommand):
    payload = {"type": "tts", "text": cmd.text}
    await devices.send_command(cmd.device_id, payload)
    return {"status": "sent"}

# Optional: health check
@app.get("/health")
async def health():
    return {"status": "ok", "devices_connected": len(devices.command_sockets)}