import os

SERVER_HOST = os.getenv("JARVIS_SERVER_HOST", "192.168.1.100")  # your main PC/server IP
SERVER_PORT = int(os.getenv("JARVIS_SERVER_PORT", "8000"))
DEVICE_ID   = os.getenv("JARVIS_DEVICE_ID", "kyan-glasses-01")

AUDIO_WS_URL   = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws/audio?device_id={DEVICE_ID}"
COMMAND_WS_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws/commands?device_id={DEVICE_ID}"
HEARTBEAT_URL  = f"http://{SERVER_HOST}:{SERVER_PORT}/api/heartbeat"
TOGGLE_URL     = f"http://{SERVER_HOST}:{SERVER_PORT}/toggle"  # for translation toggle from phone

PUSHCUT_WEBHOOK = "https://api.pushcut.io/YOUR_KEY/execute?shortcut=Jarvis%20Speak&input="  # replace
NTFY_TOPIC      = "jarvis-your-unique-topic"  # fallback

MQTT_HOST = "localhost"  # Mosquitto on Pi
MQTT_PORT = 1883
MQTT_TOPIC = "owntracks/#"  # OwnTracks publishes here

MUTE_PIN = 17  # GPIO button for mute toggle
SAMPLE_RATE = 16000
BLOCK_SIZE = 480   # 30 ms @ 16kHz for WebRTC VAD