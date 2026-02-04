# tasks/heartbeat.py
import time
import logging

class HeartbeatTask:
    def __init__(self, network, audio, sensors, hud, location, settings):
        self.network = network
        self.location = location
        self.settings = settings
        self.running = True

    def run(self):
        logging.info("HeartbeatTask started.")

        while self.running:
            packet = {
                "type": "heartbeat",
                "device": self.settings.DEVICE_ID,
                "location": self.location.get(),
                "status": "online"
            }

            self.network.send(packet)
            time.sleep(self.settings.HEARTBEAT_INTERVAL)

    def stop(self):
        self.running = False
