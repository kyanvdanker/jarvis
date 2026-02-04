import os

# Server connection
SERVER_HOST = os.getenv("JARVIS_SERVER_HOST", "192.168.168.100")   # change to your server IP
SERVER_PORT = int(os.getenv("JARVIS_SERVER_PORT", "8000"))
DEVICE_ID   = os.getenv("JARVIS_DEVICE_ID", "kyan-glasses-01")

AUDIO_WS_URL   = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws/audio?device_id={DEVICE_ID}"
COMMAND_WS_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws/commands?device_id={DEVICE_ID}"
HEARTBEAT_URL  = f"http://{SERVER_HOST}:{SERVER_PORT}/api/heartbeat"
SUMMARIZE_URL  = f"http://{SERVER_HOST}:{SERVER_PORT}/summarize_session"
NUDGE_URL      = f"http://{SERVER_HOST}:{SERVER_PORT}/proactive_nudge"

# Phone output fallback
PUSHCUT_WEBHOOK = "https://api.pushcut.io/YOUR_PUSH CUT_KEY/execute?shortcut=Jarvis%20Speak&input="  # ← replace
NTFY_TOPIC      = "jarvis-yourname"   # ← change to your topic

# MQTT for location (OwnTracks → Mosquitto on Pi)
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "owntracks/#"

# Hardware & audio
MUTE_PIN = 17               # GPIO button (pull-up, press = LOW)
SAMPLE_RATE = 16000
BLOCK_SIZE = 480            # 30 ms blocks for webrtcvad