# server/main.py
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from state import DeviceManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = FastAPI()
devices = DeviceManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# server/main.py (continued)
from fastapi import WebSocket, WebSocketDisconnect, Query

@app.websocket("/ws/audio")
async def ws_audio(websocket: WebSocket, device_id: str = Query(...)):
    await websocket.accept()
    logging.info(f"[audio] Device {device_id} connected")

    try:
        while True:
            data = await websocket.receive_bytes()
            # TODO: push `data` into your ASR/LLM pipeline
            # e.g. audio_buffer[device_id].append(data)
    except WebSocketDisconnect:
        logging.info(f"[audio] Device {device_id} disconnected")
    except Exception:
        logging.exception(f"[audio] Error for {device_id}")

# server/main.py (continued)
@app.websocket("/ws/commands")
async def ws_commands(websocket: WebSocket, device_id: str = Query(...)):
    await websocket.accept()
    await devices.register_command_socket(device_id, websocket)
    logging.info(f"[cmd] Device {device_id} connected")

    try:
        while True:
            # we don't expect messages from the device, but we must keep the socket alive
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        logging.info(f"[cmd] Device {device_id} disconnected")
    except Exception:
        logging.exception(f"[cmd] Error for {device_id}")
    finally:
        await devices.unregister_command_socket(device_id)
