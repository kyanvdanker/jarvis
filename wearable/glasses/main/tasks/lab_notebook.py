# tasks/lab_notebook.py
import time
import logging

class LabNotebookTask:
    def __init__(self, network, audio, sensors, hud, location, settings):
        self.network = network
        self.sensors = sensors
        self.location = location
        self.settings = settings
        self.running = True

        self.active = False
        self.session_id = None
        self.last_log_time = 0

        # Listen for server commands
        self.network.subscribe(self._on_server_message)

    def _on_server_message(self, data):
        if data.get("type") == "labnote_start":
            self._start_session()
        elif data.get("type") == "labnote_stop":
            self._stop_session()
        elif data.get("type") == "labnote_note":
            self._log_manual_note(data.get("text"))

    def _start_session(self):
        self.active = True
        self.session_id = int(time.time())
        logging.info(f"Lab notebook session started: {self.session_id}")

        self.network.send({
            "type": "labnote_session_start",
            "session_id": self.session_id,
            "device": self.settings.DEVICE_ID,
            "timestamp": time.time(),
            "location": self.location.get()
        })

    def _stop_session(self):
        if not self.active:
            return

        self.network.send({
            "type": "labnote_session_end",
            "session_id": self.session_id,
            "timestamp": time.time()
        })

        logging.info("Lab notebook session ended.")
        self.active = False
        self.session_id = None

    def _log_manual_note(self, text):
        if not self.active:
            return

        self.network.send({
            "type": "labnote_manual",
            "session_id": self.session_id,
            "timestamp": time.time(),
            "text": text
        })

    def run(self):
        logging.info("LabNotebookTask started.")

        while self.running:
            if not self.active:
                time.sleep(0.5)
                continue

            now = time.time()
            if now - self.last_log_time >= 60:
                self._log_environment()
                self.last_log_time = now

            time.sleep(0.2)

    def _log_environment(self):
        data = self.sensors.read()
        if not data:
            return

        packet = {
            "type": "labnote_environment",
            "session_id": self.session_id,
            "timestamp": time.time(),
            "temperature": data["temperature"],
            "pressure": data["pressure"] / 100.0,
            "location": self.location.get()
        }

        self.network.send(packet)

    def stop(self):
        self.running = False
