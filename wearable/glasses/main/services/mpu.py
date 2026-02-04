# services/mpu.py
import smbus
import time
import math
import logging

class MPUService:
    def __init__(self, settings):
        self.settings = settings
        self.bus = smbus.SMBus(1)
        self.address = 0x68

        # Wake up MPU6050
        self.bus.write_byte_data(self.address, 0x6B, 0)

        self.last_step_time = 0
        self.step_threshold = 1.2      # g-force threshold
        self.tap_threshold = 2.0       # stronger spike
        self.crash_threshold = 3.5     # very strong spike

    def read_accel(self):
        def read_word(reg):
            high = self.bus.read_byte_data(self.address, reg)
            low = self.bus.read_byte_data(self.address, reg + 1)
            val = (high << 8) + low
            return val - 65536 if val > 32767 else val

        ax = read_word(0x3B) / 16384.0
        ay = read_word(0x3D) / 16384.0
        az = read_word(0x3F) / 16384.0

        return ax, ay, az

    def detect_events(self):
        ax, ay, az = self.read_accel()
        magnitude = math.sqrt(ax*ax + ay*ay + az*az)

        events = {
            "tap": False,
            "step": False,
            "crash": False,
            "magnitude": magnitude
        }

        now = time.time()

        # Step detection (simple peak detection)
        if magnitude > self.step_threshold and (now - self.last_step_time) > 0.3:
            events["step"] = True
            self.last_step_time = now

        # Tap detection (short, sharp spike)
        if magnitude > self.tap_threshold:
            events["tap"] = True

        # Crash/fall detection (very high spike)
        if magnitude > self.crash_threshold:
            events["crash"] = True

        return events

    def stop(self):
        pass
