import json
import os
from difflib import get_close_matches

TASKS_FILE = "learned_tasks.json"

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)

def find_learned_task(text, threshold=0.8):
    tasks = load_tasks()
    triggers = [t["trigger"] for t in tasks]
    matches = get_close_matches(text.lower(), triggers, n=1, cutoff=threshold)
    if not matches:
        return None
    for t in tasks:
        if t["trigger"] == matches[0]:
            return t
    return None
