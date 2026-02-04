# services/network.py
import websocket
import json
import threading
import time
import logging

class NetworkService:
    def __init__(self, settings):
        self.settings = settings
        self.ws = None
        self.connected = False
        self.running = True
        self.listeners = []

        threading.Thread(target=self._connect_loop, daemon=True).start()

    def _connect_loop(self):
        while self.running:
            try:
                logging.info("Connecting to server...")
                self.ws = websocket.WebSocketApp(
                    self.settings.SERVER_URL,
                    on_message=self._on_message,
                    on_close=self._on_close
                )
                self.ws.run_forever()
            except Exception as e:
                logging.error(f"Network error: {e}")
            time.sleep(2)

    def _on_message(self, ws, message):
        data = json.loads(message)
        for callback in self.listeners:
            callback(data)

    def _on_close(self, ws, code, msg):
        self.connected = False
        logging.warning("Disconnected from server.")

    def send(self, packet: dict):
        try:
            if self.ws:
                self.ws.send(json.dumps(packet))
        except Exception as e:
            logging.error(f"Send failed: {e}")

    def send_command(self, action, data=None):
        packet = {
            "type": "command",
            "action": action,
            "data": data or {}
        }
        self.send(packet)


    def subscribe(self, callback):
        self.listeners.append(callback)

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
