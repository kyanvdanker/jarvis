# wearable/config.py
SERVER_HOST = "your-server-host-or-ip"
SERVER_PORT = 8000
DEVICE_ID = "kyan-glasses-01"

AUDIO_WS_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws/audio?device_id={DEVICE_ID}"
COMMAND_WS_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws/commands?device_id={DEVICE_ID}"
HEARTBEAT_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/api/heartbeat"
