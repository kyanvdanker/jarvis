# server/main.py
import json
from fastapi import FastAPI, WebSocket
from handlers.audio_handler import handle_audio
from handlers.environment_handler import handle_environment
from handlers.heartbeat_handler import handle_heartbeat
from handlers.motion_handler import handle_motion

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("Pi connected.")

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "audio_chunk":
                await handle_audio(ws, data)

            elif msg_type in ("environment_data", "storm_alert"):
                await handle_environment(ws, data)

            elif msg_type == "heartbeat":
                await handle_heartbeat(ws, data)

            elif msg_type in ("step_event", "labnote_mark", "crash_alert"):
                await handle_motion(ws, data)

    except Exception as e:
        print("Pi disconnected:", e)
