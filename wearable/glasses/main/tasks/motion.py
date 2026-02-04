# tasks/motion.py
import time
import logging

class MotionTask:
    def __init__(self, network, audio, sensors, hud, location, settings):
        from services.mpu import MPUService
        self.mpu = MPUService(settings)

        self.network = network
        self.location = location
        self.settings = settings
        self.running = True

        self.step_count = 0

    def run(self):
        logging.info("MotionTask started.")

        while self.running:
            events = self.mpu.detect_events()

            # Step detection
            if events["step"]:
                self.step_count += 1
                self.network.send({
                    "type": "step_event",
                    "device": self.settings.DEVICE_ID,
                    "steps": self.step_count,
                    "timestamp": time.time(),
                    "location": self.location.get()
                })

            # Tap detection → mark in lab notebook
            if events["tap"]:
                self.network.send({
                    "type": "labnote_mark",
                    "device": self.settings.DEVICE_ID,
                    "timestamp": time.time(),
                    "location": self.location.get()
                })

            # Crash detection → emergency alert
            if events["crash"]:
                self.network.send({
                    "type": "crash_alert",
                    "device": self.settings.DEVICE_ID,
                    "timestamp": time.time(),
                    "location": self.location.get(),
                    "magnitude": events["magnitude"]
                })

            time.sleep(0.05)

    def stop(self):
        self.running = False
