import time
import logging
import requests
import random

from config import HEARTBEAT_URL, DEVICE_ID

class Heartbeat:
    def __init__(self, interval=60):
        self.interval = interval
        self._last = 0
        self._start = time.time()

    def tick(self):
        now = time.time()
        if now - self._last < self.interval + random.uniform(0, 10):
            return
        self._last = now
        payload = {
            "device_id": DEVICE_ID,
            "uptime": int(now - self._start),
            "timestamp": int(now),
        }
        try:
            requests.post(HEARTBEAT_URL, json=payload, timeout=4)
        except Exception as e:
            logging.warning(f"[hb] fail: {e}")

    def stop(self):
        pass  # nothing needed