import asyncio
import logging
import paho.mqtt.client as mqtt
import json
import time
import requests

from config import MQTT_HOST, MQTT_PORT, MQTT_TOPIC, NUDGE_URL, DEVICE_ID

class ContextClient:
    def __init__(self):
        self.latest = {}
        self.last_nudge_check = 0
        self.client = mqtt.Client(client_id=f"jarvis-wearable-{DEVICE_ID}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        logging.info("[context] MQTT connected")
        client.subscribe(MQTT_TOPIC)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if payload.get("_type") == "location":
                self.latest = {
                    "lat": payload.get("lat"),
                    "lon": payload.get("lon"),
                    "acc": payload.get("acc", 999),
                    "batt": payload.get("batt", -1),
                    "vel": payload.get("vel", 0),
                    "tst": payload.get("tst", time.time()),
                }
                logging.debug(f"[location] {self.latest}")
        except Exception as e:
            logging.error(f"[context] parse error: {e}")

    def start(self):
        self.client.connect(MQTT_HOST, MQTT_PORT, 60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def tick(self):
        now = time.time()
        if now - self.last_nudge_check < 60:
            return
        self.last_nudge_check = now

        if not self.latest:
            return

        lat = self.latest["lat"]
        lon = self.latest["lon"]
        vel = self.latest["vel"]

        nudge_text = None

        # Example simple triggers – expand with real geo-fences or APIs later
        if vel > 5:  # km/h
            nudge_text = f"Moving at ~{vel*3.6:.0f} km/h near {lat:.4f}, {lon:.4f}. Need anything?"
        elif abs(lat - 37.7749) < 0.02 and abs(lon + 122.4194) < 0.02:  # example area
            nudge_text = "Near city center – coffee or quick stop?"

        if nudge_text:
            try:
                requests.post(
                    NUDGE_URL,
                    json={"device_id": DEVICE_ID, "text": nudge_text},
                    timeout=5
                )
                logging.info(f"[nudge] Sent: {nudge_text}")
            except Exception as e:
                logging.error(f"[nudge] failed: {e}")