import time
import logging
import requests

from config import SUMMARIZE_URL, DEVICE_ID

class MemoryManager:
    def __init__(self, silence_timeout=45):
        self.silence_timeout = silence_timeout
        self.last_voice_time = 0
        self.session_active = False
        self.session_start = 0

    def tick(self, is_speech: bool):
        now = time.time()

        if is_speech:
            self.last_voice_time = now
            if not self.session_active:
                logging.info("[memory] New session started")
                self.session_active = True
                self.session_start = now
        elif self.session_active and now - self.last_voice_time > self.silence_timeout:
            duration = now - self.session_start
            logging.info(f"[memory] Session ended ({duration:.0f}s) → requesting summary")
            self.session_active = False
            self._request_summary(duration)

    def _request_summary(self, duration: float):
        try:
            r = requests.post(
                SUMMARIZE_URL,
                json={
                    "device_id": DEVICE_ID,
                    "duration": duration,
                    "start_time": self.session_start
                },
                timeout=6
            )
            if r.status_code == 200:
                logging.info("[memory] Summary requested successfully")
            else:
                logging.warning(f"[memory] Summary request failed: {r.status_code}")
        except Exception as e:
            logging.error(f"[memory] Could not request summary: {e}")