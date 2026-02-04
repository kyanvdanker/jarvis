# server_pi.py
import logging
import json
import os
import time
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from ollama_client import ask_ollama  # or your AI function

# Ollama integration - adjust import/path to match your actual ollama_client.py
ollama = ask_ollama()  # or ollama = Ollama(model="llama3.1") etc.

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

# In-memory device management
class DeviceManager:
    def __init__(self):
        self.command_sockets: Dict[str, WebSocket] = {}

    async def register_command_socket(self, device_id: str, ws: WebSocket):
        self.command_sockets[device_id] = ws
        logging.info(f"Registered command socket for {device_id}")

    async def unregister_command_socket(self, device_id: str):
        self.command_sockets.pop(device_id, None)
        logging.info(f"Unregistered command socket for {device_id}")

    async def send_command(self, device_id: str, payload: dict):
        ws = self.command_sockets.get(device_id)
        if ws:
            try:
                await ws.send_json(payload)
                logging.info(f"Sent {payload.get('type')} to {device_id}")
            except Exception as e:
                logging.error(f"Failed to send to {device_id}: {e}")
                await self.unregister_command_socket(device_id)
        else:
            logging.warning(f"Device {device_id} not connected for command")

devices = DeviceManager()

# File for saving summaries
SUMMARY_FILE = "conversation_summaries.json"

# ────────────────────────────────────────────────
# Audio WebSocket – receives raw audio from Pi
# ────────────────────────────────────────────────
@app.websocket("/ws/audio")
async def ws_audio(websocket: WebSocket, device_id: str = Query(...)):
    await websocket.accept()
    logging.info(f"[audio] Device {device_id} connected")

    # Optional: buffer audio here for later transcription
    # audio_buffer = []  # list of bytes

    try:
        while True:
            data = await websocket.receive_bytes()
            # audio_buffer.append(data)  # accumulate for whisper
            # For now just log
            logging.debug(f"[audio] {len(data)} bytes from {device_id}")
    except WebSocketDisconnect:
        logging.info(f"[audio] Device {device_id} disconnected")
    except Exception as e:
        logging.exception(f"[audio] Error for {device_id}")

# ────────────────────────────────────────────────
# Commands WebSocket – server pushes TTS/notify to Pi
# ────────────────────────────────────────────────
@app.websocket("/ws/commands")
async def ws_commands(websocket: WebSocket, device_id: str = Query(...)):
    await websocket.accept()
    await devices.register_command_socket(device_id, websocket)
    logging.info(f"[commands] Device {device_id} connected")

    try:
        while True:
            # Keep connection alive (client rarely sends data)
            await websocket.receive_text()
    except WebSocketDisconnect:
        logging.info(f"[commands] Device {device_id} disconnected")
    except Exception as e:
        logging.exception(f"[commands] Error for {device_id}")
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
    logging.info(f"[heartbeat] {payload.device_id} uptime={payload.uptime:.1f}s")
    return {"status": "ok"}

# ────────────────────────────────────────────────
# Summarize session – called by Pi after silence
# ────────────────────────────────────────────────
class SummaryRequest(BaseModel):
    device_id: str
    duration: float = 0.0
    start_time: float = 0.0

@app.post("/summarize_session")
async def summarize_session(req: SummaryRequest):
    device_id = req.device_id

    # Placeholder transcript – replace with real whisper processing
    # In production: use audio_buffer[device_id], run whisper, get text
    transcript = (
        "User: We need to finish the CAD integration by Friday. "
        "Response: Yes, let's prioritize that and test on the Pi."
    )

    prompt = f"""
You are Jarvis, a concise and helpful assistant.
Summarize this conversation in 3–6 bullet points.
Include:
- Main topics
- Key decisions
- Action items / follow-ups
- Any names, dates, or important details

Transcript:
{transcript}

Summary (bullet points):
"""

    try:
        response = ollama.chat(
            model="llama3.1",  # or your model
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3}
        )
        summary_text = response['message']['content'].strip()
    except Exception as e:
        logging.error(f"Ollama failed: {e}")
        summary_text = "Could not generate summary at this time."

    # Save summary
    entry = {
        "timestamp": time.time(),
        "device_id": device_id,
        "duration_seconds": req.duration,
        "start_time": req.start_time,
        "transcript": transcript,
        "summary": summary_text
    }

    summaries = []
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE, "r") as f:
            summaries = json.load(f)
    summaries.append(entry)
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summaries, f, indent=2)

    logging.info(f"Saved summary for {device_id}: {summary_text[:80]}...")

    # Send to phone via Pi
    await devices.send_command(device_id, {
        "type": "tts",
        "text": f"Conversation summary: {summary_text}"
    })

    return {"status": "summary generated and saved"}

# ────────────────────────────────────────────────
# Proactive nudge – called by Pi when location triggers
# ────────────────────────────────────────────────
class NudgeRequest(BaseModel):
    device_id: str
    text: str

@app.post("/proactive_nudge")
async def proactive_nudge(req: NudgeRequest):
    device_id = req.device_id
    original_text = req.text

    prompt = f"""
You are Jarvis. Make this location-based reminder natural, short,
and helpful. Max 20 words.

Original: {original_text}

Refined:
"""

    try:
        response = ollama.chat(
            model="llama3.1",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.4}
        )
        refined_text = response['message']['content'].strip()
    except:
        refined_text = original_text

    await devices.send_command(device_id, {
        "type": "tts",
        "text": refined_text
    })

    return {"status": "nudge sent"}

# ────────────────────────────────────────────────
# Phone control endpoint (for Shortcuts)
# ────────────────────────────────────────────────
@app.get("/control")
async def control_pi(
    action: str = Query(...),
    value: str = Query(None),
    device_id: str = Query("kyan-glasses-01")
):
    if action == "mute":
        state = value.lower() in ("on", "true", "1", "yes")
        await devices.send_command(device_id, {"type": "mute", "state": state})
        return {"status": "sent", "action": "mute", "state": state}

    elif action == "toggle_translation":
        enabled = value.lower() in ("on", "true", "1", "yes") if value else True
        # You can store this globally or per-device
        await devices.send_command(device_id, {
            "type": "notify",
            "message": f"Translation {'enabled' if enabled else 'disabled'}"
        })
        return {"status": "sent", "translation": enabled}

    return JSONResponse({"error": "Unknown action"}, status_code=400)

# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "connected_devices": len(devices.command_sockets)}