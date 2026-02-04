import json
import os
from datetime import datetime

MEMORY_FILE = "memory.json"
routine_last_trigger = {}

_default_memory = {
    "user_profile": {
        "name": "Kyan"
    },
    "emotion": {
        "baseline": "neutral",
        "history": []  # list of {"emotion": str, "time": iso}
    },
    "habits": {
        "intents": []  # list of {"intent": str, "time": iso}
    },
    "health": {
        "stress_score": 0.0,
        "fatigue_score": 0.0
    }
}

_memory = None


def _load():
    global _memory
    if _memory is not None:
        return _memory

    if not os.path.exists(MEMORY_FILE):
        _memory = _default_memory.copy()
        return _memory

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        _memory = json.load(f)
    return _memory


def _save():
    if _memory is None:
        return
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(_memory, f, indent=2)


def log_intent(intent: str):
    mem = _load()
    mem["habits"]["intents"].append({
        "intent": intent,
        "time": datetime.now().isoformat()
    })
    # keep it light
    if len(mem["habits"]["intents"]) > 300:
        mem["habits"]["intents"] = mem["habits"]["intents"][-300:]
    _save()


def log_emotion(emotion: str):
    mem = _load()
    mem["emotion"]["history"].append({
        "emotion": emotion,
        "time": datetime.now().isoformat()
    })
    if len(mem["emotion"]["history"]) > 300:
        mem["emotion"]["history"] = mem["emotion"]["history"][-300:]
    _save()


def set_baseline_emotion(emotion: str):
    mem = _load()
    mem["emotion"]["baseline"] = emotion
    _save()


def get_baseline_emotion() -> str:
    mem = _load()
    return mem["emotion"].get("baseline", "neutral")


def update_health(stress_delta: float = 0.0, fatigue_delta: float = 0.0):
    mem = _load()
    h = mem["health"]
    h["stress_score"] = max(0.0, min(1.0, h["stress_score"] + stress_delta))
    h["fatigue_score"] = max(0.0, min(1.0, h["fatigue_score"] + fatigue_delta))
    _save()
    return h["stress_score"], h["fatigue_score"]


def get_health():
    mem = _load()
    return mem["health"]["stress_score"], mem["health"]["fatigue_score"]


def predict_next_intent():
    mem = _load()
    intents = mem["habits"]["intents"]
    if len(intents) < 5:
        return None
    last = intents[-1]["intent"]
    count = sum(1 for i in intents[-50:] if i["intent"] == last)
    if count >= 3:
        return last
    return None


def log_routine_event(event_name):
    mem = _load()
    if "routine" not in mem:
        mem["routine"] = {}

    now = datetime.now()
    hour = now.hour
    minute = now.minute

    if event_name not in mem["routine"]:
        mem["routine"][event_name] = []

    mem["routine"][event_name].append({
        "hour": hour,
        "minute": minute,
        "time": now.isoformat()
    })

    # keep last 50 entries
    mem["routine"][event_name] = mem["routine"][event_name][-50:]
    _save()

def is_routine_time(event_name, tolerance_minutes=20):
    mem = _load()
    if "routine" not in mem or event_name not in mem["routine"]:
        return False

    now = datetime.now()
    today = now.date()

    # Check if already triggered today
    if routine_last_trigger.get(event_name) == today:
        return False

    now_minutes = now.hour * 60 + now.minute

    times = [
        r["hour"] * 60 + r["minute"]
        for r in mem["routine"][event_name]
    ]

    if not times:
        return False

    avg = sum(times) / len(times)

    if abs(now_minutes - avg) <= tolerance_minutes:
        routine_last_trigger[event_name] = today
        return True

    return False
