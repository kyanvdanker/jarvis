# helpers.py

from datetime import datetime
import uuid
import re
import threading
import os
import csv
import time
from datetime import datetime, timedelta
import pythoncom

OUTPUT_MODE = "local"   # or "remote"
last_remote_output = None
UI_STATE = "main"
speaker_check_state = False
speaker_verified = False
emotion_learning_state = {
    "active": False,
    "history": [],
    "last_update": None
}



def set_remote_output(text: str):
    global last_remote_output
    last_remote_output = text

def pop_remote_output():
    global last_remote_output
    out = last_remote_output
    last_remote_output = None
    return out


reminder_state = {
    "active": False,
    "stage": None,              # "what" → "when"
    "message": "",              # What to remind about
    "trigger": None             # datetime when to trigger
}

REMINDER_FILE = "reminders.csv"

def extract_number(text):
    m = re.search(r"(\d+(\.\d+)?)", text)
    if not m:
        return None
    return float(m.group(1))

def generate_filename(component_name: str) -> str:
    unique_id = uuid.uuid4().hex[:8]
    return f"{component_name}_{unique_id}.stl"

class ReminderManager:
    def __init__(self, speak_callback):
        self.speak = speak_callback
        self.lock = threading.Lock()
        self.reminders = []
        self.load()
        threading.Thread(target=self.loop, daemon=True).start()

    def load(self):
        if not os.path.exists(REMINDER_FILE):
            return
        with open(REMINDER_FILE, newline="") as f:
            reader = csv.DictReader(f)
            self.reminders = list(reader)

    def save(self):
        with open(REMINDER_FILE, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "trigger_time", "message", "triggered"]
            )
            writer.writeheader()
            writer.writerows(self.reminders)

    def add_in(self, minutes, message):
        trigger = datetime.now() + timedelta(minutes=minutes)
        self.add_at(trigger, message)

    def add_at(self, dt, message):
        with self.lock:
            self.reminders.append({
                "id": str(uuid.uuid4()),
                "trigger_time": dt.isoformat(),
                "message": message,
                "triggered": "0"
            })
            self.save()

    def loop(self):
        pythoncom.CoInitialize()
        while True:
            now = datetime.now()
            with self.lock:
                changed = False
                for r in self.reminders:
                    if r["triggered"] == "1":
                        continue
                    t = datetime.fromisoformat(r["trigger_time"])
                    if now >= t:
                        self.speak(f"Reminder: {r['message']}")
                        r["triggered"] = "1"
                        changed = True
                if changed:
                    self.save()
            time.sleep(1)