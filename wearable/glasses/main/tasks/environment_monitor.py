# tasks/environment_monitor.py
import time
import logging
from collections import deque

class EnvironmentMonitorTask:
    def __init__(self, network, audio, sensors, hud, location, settings):
        self.sensors = sensors
        self.settings = settings
        self.network = network
        self.running = True

        from services.notify import NotificationService
        self.notify = NotificationService(settings)

        self.pressure_history = deque(maxlen=30)
        self.last_hydration_alert = 0
        self.last_temp_alert = 0

    def run(self):
        logging.info("EnvironmentMonitorTask started.")

        while self.running:
            data = self.sensors.read()
            if not data:
                time.sleep(5)
                continue

            temp = data["temperature"]
            pressure = data["pressure"] / 100.0
            altitude = data["altitude"]

            self.pressure_history.append(pressure)

            # Send raw data to server
            packet = {
                "type": "environment_data",
                "device": self.settings.DEVICE_ID,
                "temperature": temp,
                "pressure": pressure,
                "altitude": altitude,
                "location": self.location.get(),
                "timestamp": time.time()
            }
            self.network.send(packet)

            # Lab notebook hook
            self.network.send({
                "type": "labnote_environment",
                "device": self.settings.DEVICE_ID,
                "temperature": temp,
                "pressure": pressure,
                "timestamp": time.time()
            })

            # Storm detection
            self._check_for_storm(pressure)

            # Hydration + temperature wellness
            self._check_temperature_wellness(temp)

            time.sleep(60)

    def _check_temperature_wellness(self, temp):
        now = time.time()

        # Hydration reminder every 2 hours
        if now - self.last_hydration_alert > 7200:
            self.notify.send("💧 Hydration Reminder", "Take a sip of water.")
            self.last_hydration_alert = now

        # Heat stress
        if temp > 28 and now - self.last_temp_alert > 1800:
            self.notify.send("🔥 Heat Alert", f"It's {temp:.1f}°C. Stay cool and hydrated.")
            self.last_temp_alert = now

        # Cold stress
        if temp < 10 and now - self.last_temp_alert > 1800:
            self.notify.send("❄️ Cold Alert", f"It's {temp:.1f}°C. Dress warm.")
            self.last_temp_alert = now

    def _check_for_storm(self, pressure):
        if len(self.pressure_history) < 10:
            return

        old_pressure = self.pressure_history[0]
        drop = old_pressure - pressure

        low_pressure = pressure < 1000
        rapid_drop = drop > 4

        if low_pressure and rapid_drop:
            self._send_storm_alert(pressure, drop)

    def _send_storm_alert(self, pressure, drop):
        title = "⚠️ Storm Warning"
        msg = f"Pressure dropped {drop:.1f} hPa. Current: {pressure:.1f} hPa. Storm likely."

        logging.warning(msg)
        self.notify.send(title, msg)

        self.network.send({
            "type": "storm_alert",
            "device": self.settings.DEVICE_ID,
            "pressure": pressure,
            "drop": drop,
            "location": self.location.get(),
            "timestamp": time.time()
        })

    def stop(self):
        self.running = False
