from openwakeword import Model
import sounddevice as sd
import numpy as np
import keyboard
import subprocess
import wave
import time
import os                        
from interpreter import interpret_command
from cad_executor import run_cad_code
from viewer import rotate_view, reset_view, show_object
from gui_viewer import rotate_camera, zoom_camera, reset_camera, start_viewer, load_stl_into_viewer
import threading
import requests
import pyttsx3 
from ollama_client import call_ollama, ask_ollama, stream_ollama
import pvporcupine
import sounddevice as sd
import numpy as np
import threading
import queue
import csv
import uuid
import difflib
from datetime import datetime, timedelta
import re
from cad_dialog import start_cad_creation, continue_cad_dialog, cad_state, modify_last_part
from cad_intent import detect_cad_component, wants_creation
from project_manager import create_project, current_project, switch_project, list_projects, add_note, read_notes, ROOT_DIR
from printer import send_to_printer
from vision.camera_control import start_gesture_camera
from calander_manager import get_todays_events, planning_state, get_briefing, start_planning, continue_planning
from speak import speak, stop_speaking
import logging
from word2number import w2n
from intent_classifier.intent_classifier import classify_intent_ml
from simulation_dialog import (
    start_simulation_dialog,
    continue_simulation_dialog,
    simulation_state
)



logging.basicConfig(filename='jarvis_errors.log', level=logging.INFO)

tts_queue = queue.Queue()
tts_running = True

REMINDER_FILE = "reminders.csv"

porcupine = pvporcupine.create(
    access_key="SwRSMQXziSaF9ZcqpSgZDUpUW8HusjVIo8CWwmFsFVsW8vrP8H8mew==",
    keywords=["jarvis"]
)

wake_detected = False
porcupine_running = True
suggestion = False

tts_engine = pyttsx3.init()
tts_engine.setProperty('voice', 'Microsoft Jenny Natural - English (United States)')
tts_engine.setProperty('rate', 160)   # optional but often helps

conversation_history = []
MAX_HISTORY = 10   # last 6 exchanges (user + assistant)

interrupt_requested = threading.Event()
last_command = ""

SAMPLE_RATE = 16000
CHANNELS = 1
MODEL_PATH = r"C:\whisper\models\ggml-base.en.bin"
WHISPER_EXE = r"C:\whisper\whisper-cli.exe"

tts_buffer = ""

reminder_state = {
    "active": False,
    "stage": None,              # "what" → "when"
    "message": "",              # What to remind about
    "trigger": None             # datetime when to trigger
}

last_suggestions = []

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


def is_view_command(text):
    t = text.lower()
    return any(cmd in t for cmd in [
        "rotate left", "rotate right",
        "rotate up", "rotate down",
        "zoom in", "zoom out",
        "reset view", "reset camera"
    ])

CAD_COMPONENTS_KEYWORDS = {
    "motor_casing": ["motor", "motor casing", "casing"],
    "nozzle": ["nozzle"],
    "fin_canister": ["fin canister", "fin tube", "fin holder"],
    "bulkhead": ["bulkhead", "disc", "plate"],
    "engine_mount": ["engine mount", "mount"],
    "body_tube": ["body tube", "tube", "rocket tube"],
    "nose_cone": ["nose cone", "cone", "nose"]
}

def detect_cad_component(text: str):
    t = text.lower()
    for comp, keywords in CAD_COMPONENTS_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return comp
    return None

def add_training_example(sentence, intent):
    with open("intent_classifier/intent_data.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([sentence, intent])


def ask_ollama_stream(prompt: str, model: str = "llama3"):
    try:
        buffer = ""
        for token in stream_ollama(prompt, model=model):
            buffer += token
            if len(buffer) > 45 or any(p in token for p in ".,!?;:"):  # simple chunking
                speak(buffer.strip())
                buffer = ""
        if buffer:
            speak(buffer.strip())
    except Exception as e:
        print("Streaming error:", e)
        speak("There was an error streaming the response.")

def generate_filename(component_name: str) -> str:
    """
    Generates a unique filename for a CAD object export.
    Example: motor_casing_3f2b1e8a.stl
    """
    unique_id = uuid.uuid4().hex[:8]  # short unique ID
    return f"{component_name}_{unique_id}.stl"

def clean_text_for_classification(text: str) -> str:
    # Keep letters, numbers, spaces — nothing else
    return re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()

def parse_reminder_command(text):
    t = text.lower()

    m = re.search(r"in (\d+) minute", t)
    if m:
        return ("in", int(m.group(1)), text)

    m = re.search(r"at (\d{1,2}):(\d{2})", t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        now = datetime.now()
        trigger = now.replace(hour=hour, minute=minute, second=0)
        if trigger < now:
            trigger += timedelta(days=1)
        return ("at", trigger, text)

    return None

def extract_number(text):
    m = re.search(r"(\d+(\.\d+)?)", text)
    if not m:
        return None
    return float(m.group(1))

def convert_words_to_numbers(text: str) -> str:
    try:
        # Try to convert any number phrase
        words = text.split()
        for i, word in enumerate(words):
            try:
                num = w2n.word_to_num(word)
                words[i] = str(num)
            except:
                pass  # not a number word
        return ' '.join(words)
    except:
        return text

def interpret_command_from_state(state):
    # TEMP: convert state into a text command
    if state["component"] == "motor_casing":
        p = state["params"]
        return f"create motor casing inner {p['inner_d']} outer {p['outer_d']} length {p['length']}"
    return None

def porcupine_listener(access_key):
    global wake_detected

    porcupine = pvporcupine.create(
        access_key=access_key,
        keywords=["jarvis"]
    )

    frame_length = porcupine.frame_length
    sample_rate = porcupine.sample_rate

    with sd.InputStream(
        channels=1,
        samplerate=sample_rate,
        blocksize=frame_length,
        dtype='int16'
    ) as stream:
        while True:
            pcm, _ = stream.read(frame_length)
            pcm = np.frombuffer(pcm, dtype=np.int16)

            if porcupine.process(pcm) >= 0:
                print("\nWake word detected!")
                wake_detected = True

def add_to_history(role, text):
    conversation_history.append({"role": role, "text": text})
    if len(conversation_history) > MAX_HISTORY:
        conversation_history.pop(0)

def build_history_text():
    return "\n".join([f"{h['role']}: {h['text']}" for h in conversation_history])

def handle_view_commands(text):
    t = text.lower()

    # Rotation
    if "rotate left" in t:
        rotate_camera(dx=-10)
        return True

    if "rotate right" in t:
        rotate_camera(dx=10)
        return True

    if "rotate up" in t:
        rotate_camera(dy=10)
        return True

    if "rotate down" in t:
        rotate_camera(dy=-10)
        return True

    # Zoom
    if "zoom in" in t:
        zoom_camera(0.9)   # closer
        return True

    if "zoom out" in t:
        zoom_camera(1.1)   # farther
        return True

    # Reset
    if "reset view" in t or "reset camera" in t:
        reset_camera()
        return True

    return False

def is_general_question(text):
    t = text.lower()
    return (
        t.startswith("what") or
        t.startswith("who") or
        t.startswith("when") or
        t.startswith("why") or
        t.startswith("how") or
        "explain" in t or
        "tell me about" in t
    )

def record_audio():
    print("Hold SPACE to talk...")
    while not keyboard.is_pressed("space"):
        time.sleep(0.01)

    print("Recording...")
    frames = []

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS) as stream:
        while keyboard.is_pressed("space"):
            data, _ = stream.read(1024)
            frames.append(data.copy())

    print("Stopped recording.")

    audio = np.concatenate(frames, axis=0)

    with wave.open("audio.wav", "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())

    return "audio.wav"

def record_audio_until_silence(
    silence_threshold=0.01,
    silence_duration=0.8,
    chunk=1024
):
    print("Listening...")

    frames = []
    silence_start = None

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS) as stream:
        while True:
            data, _ = stream.read(chunk)
            frames.append(data.copy())

            volume = np.abs(data).mean()

            if volume < silence_threshold:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > silence_duration:
                    break
            else:
                silence_start = None

    print("Stopped listening.")

    audio = np.concatenate(frames, axis=0)

    with wave.open("audio.wav", "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())

    return "audio.wav"


def transcribe(audio_file):
    try:
        cmd = [WHISPER_EXE, "-m", MODEL_PATH, "-f", audio_file, "--no-timestamps"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)  # Add timeout to prevent hangs
        if result.returncode != 0:
            raise ValueError(f"Whisper failed with code {result.returncode}: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        logging.error(f"Transcription error: {e}")
        return None  # Return None on failure

def wants_creation(text: str) -> bool:
    t = text.lower()
    return any(word in t for word in [
        "create",
        "make",
        "generate",
        "build",
        "design"
    ])


def create_cad_object():
    code = interpret_command_from_state(cad_state)
    result, err = run_cad_code(code)

    if err:
        speak("There was an error creating the part.")
        reset_cad_state()
        return

    # Ensure project is selected
    if current_project is None:
        speak("No project selected. CAD file will not be saved.")
        return

    # Create cad_files folder if it doesn't exist
    project_path = os.path.join(ROOT_DIR, current_project, "cad_files")
    os.makedirs(project_path, exist_ok=True)

    # Generate unique filename and full path
    filename = generate_filename(cad_state["component"])
    path = os.path.join(project_path, filename)

    # Export STL
    result.val().exportStl(path)

    # Show in viewer
    show_object(result)
    load_stl_into_viewer(path)
    speak(f"{cad_state['component']} created in project '{current_project}'.")


    show_object(result)
    load_stl_into_viewer(path)

    speak("Part created.")
    reset_cad_state()

def reset_cad_state():
    cad_state.update({
        "active": False,
        "stage": None,
        "component": None,
        "params": {},
        "dry_run": False
    })

def extract_print_target(text):
    return text.lower().replace("print", "").strip()

def find_best_matching_stl(target_name):
    if current_project is None:
        return None, "No project selected."

    project_path = os.path.join(ROOT_DIR, current_project, "cad_files")
    if not os.path.exists(project_path):
        return None, "This project has no CAD files."

    files = [f for f in os.listdir(project_path) if f.lower().endswith(".stl")]
    if not files:
        return None, "No STL files found in this project."

    match = difflib.get_close_matches(target_name, files, n=1, cutoff=0.2)
    if not match:
        return None, "No matching file found."

    return os.path.join(project_path, match[0]), None

def start_reminder_dialog():
    reminder_state["active"] = True
    reminder_state["stage"] = "what"
    speak("Sure, what would you like me to remind you about?")

def continue_reminder_dialog(text):
    if reminder_state["stage"] == "what":
        reminder_state["message"] = text.strip()
        reminder_state["stage"] = "when"
        speak(f"Got it — remind you about '{text}'. When should I remind you? "
              "Say something like 'in 30 minutes' or 'at 3:45'.")

    elif reminder_state["stage"] == "when":
        parsed = parse_reminder_command(text)
        if parsed:
            kind, value, _ = parsed
            if kind == "in":
                trigger = datetime.now() + timedelta(minutes=value)
            else:  # "at"
                trigger = value

            reminder_state["trigger"] = trigger

            # Actually set the reminder
            reminder_manager.add_at(trigger, reminder_state["message"])
            
            time_str = trigger.strftime("%H:%M %p on %A")
            speak(f"Reminder set! I'll remind you about '{reminder_state['message']}' "
                  f"at {time_str}.")

            # Reset state
            reminder_state["active"] = False
            reminder_state["stage"] = None
            reminder_state["message"] = ""
            reminder_state["trigger"] = None

        else:
            speak("Sorry, I didn't understand the time. "
                  "Try again like 'in 20 minutes' or 'at 5:30'.")
            # Stay in "when" stage — don't reset

def classify_intent(text: str) -> str:
    t = text.lower()

    if text.lower().startswith("print "):
        return "print"
    if "create project" in t:
        return "create_project"
    if "switch project" in t:
        return "switch_project"
    if "list projects" in t:
        return "list_projects"
    if "add note" in t or "memo" in t:
        return "add_note"
    if "read notes" in t:
        return "read_notes"
    if "camera mode" in t:
        return "mode_camera"
    if "object mode" in t:
        return "mode_object"
    if "rotate mode" in t:
        return "mode_rotate"
    if "zoom mode" in t:
        return "mode_zoom"
    
    if planning_state["active"]:
        return "planning_followup"
    if "plan project" in t or "new project plan" in t:
        return "planning_start"

    if "what's happening today" in t or "what is happening today" in t:
        return "agenda_today"

    if cad_state["active"]:
        return "cad_followup"

    if handle_view_commands(text):
        return "view"

    if reminder_state["active"]:
        return "reminder_followup"

    if parse_reminder_command(text):
        return "reminder"
    elif "remind" in t or "reminder" in t or "set reminder" in t:
        return "reminder_start"

    if wants_creation(text):
        component_name = detect_cad_component(text)
        if component_name:
            return "cad_start"

    if is_general_question(text):
        return "question"
    
    if "good morning" in t or "daily briefing" in t or "what's my day" in t:
        return "briefing"

    return "unknown"

def start_cad_creation(component_name: str, dry_run: bool = False):
    cad_state["active"] = True
    cad_state["stage"] = "collecting"
    cad_state["params"] = {}
    cad_state["dry_run"] = dry_run

    # Improved detection
    detected = detect_cad_component(component_name)
    if detected:
        cad_state["component"] = detected
        speak(f"Creating {detected.replace('_', ' ')}. "
              "What are the main parameters? (e.g., inner diameter, length...)")
        if dry_run:
            speak("(Dry run mode enabled - no file will be saved)")
    else:
        speak("I don't know what component that is. "
              "Try 'motor casing', 'nozzle', or another known part.")
        cad_state["active"] = False

def main():
    print("Push-to-talk STT ready.")
    pending_sentence = None

    # Start wake-word listener
    threading.Thread(
        target=porcupine_listener,
        args=("SwRSMQXziSaF9ZcqpSgZDUpUW8HusjVIo8CWwmFsFVsW8vrP8H8mew==",),
        daemon=True
    ).start()

    global reminder_manager, last_suggestions, suggestion

    reminder_manager = ReminderManager(speak)

    print("Wake word ready")

    global wake_detected, porcupine_running

    while True:
        # --- WAIT FOR WAKE WORD OR SPACE ---
        if wake_detected:
            wake_detected = False
            speak("Yes, Kyan?")
            time.sleep(1.2)
            audio_file = record_audio_until_silence()

        elif keyboard.is_pressed("space"):
            audio_file = record_audio()

        else:
            time.sleep(0.01)
            continue

        # --- TRANSCRIBE ---
        text = transcribe(audio_file)
        if text is None:
            speak("Sorry, I couldn't understand that—maybe speak clearer? Trying again.")
            audio_file = record_audio_until_silence()  # Auto-retry once
            text = transcribe(audio_file)
            if text is None:
                speak("Still having trouble. Let's try later.")
                continue

        clean_text = clean_text_for_classification(text)
        clean_text = convert_words_to_numbers(clean_text)
        print("\nYou said:", text, "\n")
        print("\nCleaned text:", clean_text)
        text = clean_text  # Note: You might want to keep raw 'text' for Ollama prompts

        if not text:
            speak("Sorry, I didn't hear anything. Want to try again?")
            continue  # Or add a yes/no confirmation
        
        if any(word in clean_text for word in ["shut up", "stop", "quiet", "stop talking", "be quiet", "silence", "enough"]):
            stop_speaking()
            speak("Okay, I'm quiet now.")
            time.sleep(0.3)
            continue

        confidence = 1

        # 1. Rule-based overrides FIRST
        if cad_state["active"]:
            intent = "cad_followup"
        elif reminder_state["active"]:
            intent = "reminder_followup"
        elif planning_state["active"]:
            intent = "planning_followup"
        elif handle_view_commands(text):
            intent = "view"
        elif suggestion:
            intent = "suggestion"
        elif simulation_state["active"]:
            intent = "simulation_followup"
        else:
            # 2. ML classifier for everything else
            intent, confidence, ranked = classify_intent_ml(text)

        print(intent)


        if confidence < 0.45:
            print(confidence)
            suggestions = [i for i, p in ranked[:3]]
            last_suggestions = suggestions
            pending_sentence = text
            speak(f"I'm not sure. Did you mean {suggestions[0]}, {suggestions[1]}, or {suggestions[2]}")
            suggestion = True
            continue

        elif last_suggestions and intent == "suggestion" and any(phrase in clean_text for phrase in 
            ["yes", "yeah", "that", "correct", "the first", "first one", "second", "third"]):

            if not last_suggestions:
                speak("Sorry, I don't remember what I suggested.")
                continue

            # Determine which suggestion user meant
            choice = None
            if any(x in clean_text for x in ["first", "1st", "one", "1"]):
                choice = last_suggestions[0]
            elif any(x in clean_text for x in ["second", "2nd", "two", "2"]):
                choice = last_suggestions[1] if len(last_suggestions) > 1 else last_suggestions[0]
            elif any(x in clean_text for x in ["third", "3rd", "three", "3"]):
                choice = last_suggestions[2] if len(last_suggestions) > 2 else last_suggestions[0]
            else:
                choice = last_suggestions[0]

            speak(f"Okay, doing '{choice}'.")

            # --- NEW: Self-learning ---
            if pending_sentence:
                add_training_example(pending_sentence, choice)
                pending_sentence = None

            # Clear suggestions
            last_suggestions = []

            # Re-run the command as if user said it
            text = choice
            clean_text = clean_text_for_classification(choice)

            # Map suggestion → intent
            intent_map = {
                "create project": "create_project",
                "switch project": "switch_project",
                "add note": "add_note",
                "read notes": "read_notes",
                "print": "print",
                "reminder": "reminder",
                "agenda today": "agenda_today",
                "good morning": "briefing",
                "briefing": "briefing",
                "what's my day": "briefing",
                "plan project": "planning_start",
                "simulate motor": "simulate_motor",
                "simulate_motor": "simulate_motor",
                "run simulation": "simulate_motor",
                "motor simulation": "simulate_motor",

            }

            simulated_intent = intent_map.get(choice)
            if simulated_intent:
                intent = simulated_intent
            else:
                speak("I found a match but don't know how to do it yet.")
                continue
            suggestion = False


        if intent == "view":
            handle_view_commands(text)
            continue

        elif intent == "reminder_start":
            start_reminder_dialog()
            continue

        elif intent == "simulate_motor":
            start_simulation_dialog()
            continue

        elif intent == "simulation_followup":
            continue_simulation_dialog(text)
            continue

        elif intent == "reminder_followup":
            continue_reminder_dialog(text)
            continue

        elif intent == "reminder":
            # Existing direct parsing (for when user gives full command at once)
            parsed = parse_reminder_command(text)
            if parsed:
                kind, value, original = parsed
                if kind == "in":
                    reminder_manager.add_in(value, original)
                    speak(f"Reminder set in {value} minutes.")
                else:
                    reminder_manager.add_at(value, original)
                    speak("Reminder set.")
            else:
                # If direct parse failed, fall back to multi-step
                start_reminder_dialog()
            continue

        elif intent == "question":
            history_text = build_history_text()
            prompt = f"{history_text}\nUser: {text}"
            add_to_history("User", text)

            # stream the response
            ask_ollama_stream(prompt)

            # optionally store the full answer in history
            add_to_history("Jarvis", "(streamed response)")
            continue



        if intent == "cad_start":
            # Start viewer
            threading.Thread(target=start_viewer, daemon=True).start()
            # Start gesture camera
            threading.Thread(target=start_gesture_camera, daemon=True).start()
            component_name = detect_cad_component(text)
            dry_run = "dry" in text.lower()
            start_cad_creation(component_name, dry_run)
            continue

        elif intent == "cad_followup":
            continue_cad_dialog(text)
            continue

        elif intent == "cad_modify":
            modify_last_part(text)
            continue

        elif intent == "agenda_today":
            events = get_todays_events()
            speak(events)
            continue

        elif intent == "create_project":
            project_name = text.lower().replace("create project", "").strip()
            speak(create_project(project_name))
            continue

        elif intent == "switch_project":
            project_name = text.lower().replace("switch project", "").strip()
            speak(switch_project(project_name))
            continue

        elif intent == "list_projects":
            projects = list_projects()
            if projects:
                speak("Projects: " + ", ".join(projects))
            else:
                speak("No projects found.")
            continue

        elif intent == "add_note":
            note_text = text.lower().replace("add note", "").strip()
            speak(add_note(note_text))
            continue

        elif intent == "read_notes":
            notes = read_notes()
            speak(notes)
            continue
        elif intent == "mode_camera":
            gesture_mode = "camera"
            speak("Camera mode activated.")
            continue

        elif intent == "mode_object":
            gesture_mode = "object"
            speak("Object manipulation mode activated.")
            continue
        
        elif intent == "briefing":
            briefing_text = get_briefing(reminder_manager)
            speak(briefing_text)
            continue

        elif intent == "planning_start":
            start_planning(clean_text)
            continue
        elif intent == "planning_followup":
            continue_planning(clean_text)
            continue

        elif intent == "print":
            target = extract_print_target(text)
            stl_path, err = find_best_matching_stl(target)

            if err:
                speak(err)
                continue

            speak(f"Printing {target}.")
            result = send_to_printer(stl_path)

            if result is True:
                speak("Print started.")
            else:
                speak("Failed to start print.")
            continue


        else:
            speak("Sorry, I don't understand that.")
            continue

if __name__ == "__main__":
    main()
