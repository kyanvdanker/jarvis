# services/notify.py
import requests
import logging

class NotificationService:
    def __init__(self, settings):
        self.settings = settings

    def send(self, title, message):
        try:
            requests.post(
                self.settings.NOTIFY_URL,
                data=message.encode("utf-8"),
                headers={"Title": title}
            )
        except Exception as e:
            logging.error(f"Notification failed: {e}")

    def stop(self):
        pass
