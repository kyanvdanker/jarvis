# handlers/environment_handler.py
import json
import time

async def handle_environment(ws, data):
    msg_type = data["type"]

    if msg_type == "environment_data":
        log = {
            "timestamp": data["timestamp"],
            "temperature": data["temperature"],
            "pressure": data["pressure"],
            "altitude": data["altitude"],
            "location": data["location"]
        }

        with open("storage/environment_log.json", "a") as f:
            f.write(json.dumps(log) + "\n")

    elif msg_type == "storm_alert":
        print("⚠️ Storm alert from Pi:", data)
        # You can forward this to your phone or UI
