import time
import logging

from config import COMMAND_WS_URL  # if want to send via WS; else use requests

class MemoryManager:
    def __init__(self, silence_timeout=45):
        self.silence_timeout = silence_timeout
        self.last_voice_time = 0
        self.session_active = False

    def tick(self, is_speech: bool):
        now = time.time()
        if is_speech:
            self.last_voice_time = now
            if not self.session_active:
                logging.info("[memory] New conversation session started")
                self.session_active = True
        elif self.session_active and now - self.last_voice_time > self.silence_timeout:
            logging.info("[memory] Session ended → requesting summary")
            self.session_active = False
            # Tell server to summarize
            try:
                requests.post(COMMAND_WS_URL.replace("ws://", "http://").replace("/ws/commands", "/summarize"), 
                              json={"device_id": "kyan-glasses-01"}, timeout=5)
            except Exception as e:
                logging.error(f"[memory] Summary request fail: {e}")