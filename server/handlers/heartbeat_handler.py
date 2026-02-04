# handlers/heartbeat_handler.py
import time

async def handle_heartbeat(ws, data):
    print(f"[Heartbeat] {data['device']} alive at {time.ctime()}")
    # You can store last-seen timestamps here
