# config/settings.py

class Settings:
    # Device identity
    DEVICE_ID = "wearable-pi-01"

    # Server connection
    SERVER_URL = "ws://192.168.1.100:8000/ws"   # your laptop server WebSocket

    # Audio settings
    AUDIO_RATE = 16000  # 16 kHz for speech

    # BLE adapter (if you use BLE later)
    BLE_ADAPTER = "hci0"

    # Notification service (ntfy.sh or your own server)
    NOTIFY_URL = "https://ntfy.sh/your_topic_here"

    # Heartbeat settings
    HEARTBEAT_INTERVAL = 5  # seconds
