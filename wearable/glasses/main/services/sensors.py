# services/sensors.py
import Adafruit_BMP.BMP085 as BMP085
import logging

class SensorService:
    def __init__(self, settings):
        try:
            self.sensor = BMP085.BMP085()
            self.available = True
        except Exception as e:
            logging.error(f"BMP180 init failed: {e}")
            self.available = False

    def read(self):
        if not self.available:
            return None

        return {
            "temperature": self.sensor.read_temperature(),
            "pressure": self.sensor.read_pressure(),
            "altitude": self.sensor.read_altitude()
        }

    def stop(self):
        pass
