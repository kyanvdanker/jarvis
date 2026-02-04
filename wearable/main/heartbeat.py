# wearable/heartbeat.py
import time
import logging
import requests

from config import HEARTBEAT_URL, DEVICE_ID

class Heartbeat:
    def __init__(self, interval=10):
        self.interval = interval
        self._last = 0
        self._start = time.time()

    def tick(self):
        now = time.time()
        if now - self._last < self.interval:
            return

        self._last = now
        payload = {
            "device_id": DEVICE_ID,
            "uptime": now - self._start,
            "timestamp": now,
            # later: "cpu_temp": ..., "wifi_rssi": ...
        }

        try:
            r = requests.post(HEARTBEAT_URL, json=payload, timeout=3)
            if r.status_code != 200:
                logging.warning(f"[hb] Non-200: {r.status_code}")
        except Exception:
            logging.exception("[hb] Failed")
