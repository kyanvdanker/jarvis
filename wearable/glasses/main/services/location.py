# services/location.py
import json
import logging
from bluezero import peripheral

class LocationService:
    SERVICE_UUID = "1234"
    CHAR_UUID = "5678"

    def __init__(self, settings):
        self.settings = settings
        self.current_location = None

        self.characteristic = peripheral.Characteristic(
            uuid=self.CHAR_UUID,
            properties=['write'],
            value=[],
            write_callback=self._on_write
        )

        self.service = peripheral.Service(
            uuid=self.SERVICE_UUID,
            primary=True,
            characteristics=[self.characteristic]
        )

        self.device = peripheral.Peripheral(
            adapter_addr=settings.BLE_ADAPTER,
            local_name="WearablePi",
            services=[self.service]
        )

    def _on_write(self, value, options):
        try:
            data = json.loads(value.decode())
            self.current_location = data
            logging.info(f"Location updated: {data}")
        except Exception as e:
            logging.error(f"Invalid location data: {e}")

    def get(self):
        return self.current_location

    def run(self):
        self.device.run()

    def stop(self):
        self.device.quit()
