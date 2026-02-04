import asyncio
import logging
import paho.mqtt.client as mqtt
import json
import time

from config import MQTT_HOST, MQTT_PORT, MQTT_TOPIC

class ContextClient:
    def __init__(self):
        self.latest_context = {}
        self.client = None
        self._stop = False

    def on_connect(self, client, userdata, flags, rc):
        logging.info("[context] MQTT connected")
        client.subscribe(MQTT_TOPIC)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if payload.get("_type") == "location":
                self.latest_context = {
                    "lat": payload.get("lat"),
                    "lon": payload.get("lon"),
                    "acc": payload.get("acc", 999),
                    "batt": payload.get("batt", -1),
                    "vel": payload.get("vel", 0),
                    "tst": payload.get("tst", 0),
                }
                logging.info(f"[context] Update: {self.latest_context}")
        except Exception as e:
            logging.error(f"[context] parse error: {e}")

    def start(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_HOST, MQTT_PORT, 60)
        self.client.loop_start()

    def stop(self):
        self._stop = True
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

    def tick(self):
        pass  # can add proactive here later if needed

    def get_prompt_snippet(self):
        if not self.latest_context:
            return ""
        c = self.latest_context
        return f"User location approx {c['lat']:.5f}, {c['lon']:.5f} (acc {c['acc']}m), speed {c['vel']*3.6:.1f} km/h, phone batt {c['batt']}%. "