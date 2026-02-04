# handlers/motion_handler.py
import json
import time

async def handle_motion(ws, data):
    msg_type = data["type"]

    if msg_type == "step_event":
        log = {
            "timestamp": data["timestamp"],
            "steps": data["steps"],
            "location": data["location"]
        }
        with open("storage/motion_log.json", "a") as f:
            f.write(json.dumps(log) + "\n")

    elif msg_type == "labnote_mark":
        print("📌 Lab notebook mark:", data)

    elif msg_type == "crash_alert":
        print("🚨 Crash detected:", data)
        # You can notify your phone here
