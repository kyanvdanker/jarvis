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
from calander_manager import get_todays_events, planning_state, get_briefing, start_planning, continue_planning, clear_wake_time
from speak import speak
import logging
from word2number import w2n
from intent_classifier.intent_classifier import classify_intent_ml
from simulation_dialog import (
    start_simulation_dialog,
    continue_simulation_dialog,
    simulation_state
)
from brain import process_text
import brain
import helpers
from emotion_model import detect_emotion
from speaker_model import is_kyan
from datetime import datetime, timedelta
import memory_manager as mem
import gui_main
from calander_manager import load_wake_time
import autonymous as auto
import vision.camera_control
from vision.camera_llm import camera_autonomous_check

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
wake_triggered = False


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
            now = time.time()
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
        now_dt = datetime.now()
        trigger = now_dt.replace(hour=hour, minute=minute, second=0)
        if trigger < now_dt:
            trigger += timedelta(days=1)
        return ("at", trigger, text)

    return None

def handle_speech_output(text: str):
    if helpers.OUTPUT_MODE == "local":
        speak(text)   # SAPI
    else:
        # Store the text so FastAPI can return it
        global last_remote_output
        last_remote_output = text


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

def autonomous_check():
    now = time.time()
    now_dt = datetime.fromtimestamp(now)

    # Example: if it's late and you sound tired
    stress, fatigue = mem.get_health()
    if now_dt.hour >= 22 and fatigue > 0.6:
        return "Would you like me to set a wake-up time for tomorrow?"

    # Example: if you often check agenda in the morning
    if mem.is_routine_time("check_agenda"):
        return "Do you want me to read your agenda?"

    # Example: if you haven't interacted in a while
    idle = now - vision.camera_control.last_interaction_time
    if idle > 600 and stress > 0.5:
        return "You’ve been quiet for a while. Want to take a short break?"

    return None

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
    min_record_time=5.0,
    chunk=1024
):
    print("Listening...")

    frames = []
    silence_start = None
    start_time = time.time()
    heard_voice = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS) as stream:
        while True:
            data, _ = stream.read(chunk)
            frames.append(data.copy())

            volume = np.abs(data).mean()
            now = time.time()

            # Detect if user has spoken at least once
            if volume > silence_threshold:
                heard_voice = True
                silence_start = None
            else:
                # Silence logic only applies AFTER user has spoken
                if heard_voice:
                    if silence_start is None:
                        silence_start = now
                    elif now - silence_start > silence_duration:
                        # User stopped talking → stop
                        break

            # If user never spoke → stop after minimum time
            if not heard_voice and (now - start_time) >= min_record_time:
                break

            # If user spoke → ensure at least min_record_time before stopping
            if heard_voice and (now - start_time) < min_record_time:
                continue

    print("Stopped listening.")

    audio = np.concatenate(frames, axis=0)

    with wave.open("audio.wav", "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())

    return "audio.wav"

def run_wake_sequence():
    speak("Good morning Kyan. It's time to wake up.")
    
    # Wait 2 minutes for response
    start = time.time()
    while time.time() - start < 120:
        if keyboard.is_pressed("space"):  # user responds
            speak("Good morning. You're awake.")
            clear_wake_time()
            return
        time.sleep(0.5)

    # No response → alarm
    speak("You did not respond. Starting alarm.")
    play_alarm_sound(30)
    clear_wake_time()

def play_alarm_sound(duration=30):
    import winsound
    end = time.time() + duration
    while time.time() < end:
        winsound.Beep(1000, 500)  # 1000 Hz, 0.5 sec

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

def main():
    print("Push-to-talk STT ready.")
    # Start GUI viewer in background

    # Start wake-word listener
    threading.Thread(
        target=porcupine_listener,
        args=("SwRSMQXziSaF9ZcqpSgZDUpUW8HusjVIo8CWwmFsFVsW8vrP8H8mew==",),
        daemon=True
    ).start()

    threading.Thread(target=vision.camera_control.start_gesture_camera, daemon=True).start()


    last_ambient_check = time.time()
    time.time()


    global wake_detected

    while True:

        # --- LISTENING LOGIC ---

        # --- WAKE CHECK ---
        wake_time = load_wake_time()
        if wake_time:
            now = datetime.now()
            if now >= wake_time and not wake_triggered:
                wake_triggered = True
                threading.Thread(target=run_wake_sequence, daemon=True).start()

        if not brain.autonomy_state["waiting_for_confirmation"]:
            suggestion = autonomous_check()
            if suggestion:
                brain.autonomy_state["last_suggestion"] = suggestion
                brain.autonomy_state["waiting_for_confirmation"] = True
                speak(suggestion)


        if wake_detected:
            wake_detected = False
            speak("Yes, Kyan?")
            time.sleep(1.5)
            audio_file = record_audio_until_silence()

        elif keyboard.is_pressed("space"):
            audio_file = record_audio()

        elif (
            cad_state["active"]
            or simulation_state["active"]
            or helpers.reminder_state["active"]
            or planning_state["active"]
            or brain.project_state["active"]
            or brain.whatsapp_state["active"]
            or brain.security_state
        ):
            audio_file = record_audio_until_silence()

        else:
            # ambient check every ~30 seconds
            now = time.time()
            if (now - last_ambient_check) > 30:
                last_ambient_check = now
                stress, fatigue = mem.get_health()
                idle = (now - vision.camera_control.last_interaction_time)

                if time.time() - vision.camera_control.last_seen_kyan > 300:  # 5 minutes
                    # next time camera sees you, face_id will trigger greeting
                    pass

                if idle > 300 and (stress > 0.6 or fatigue > 0.6):
                    speak("You’ve been quiet for a while and you sounded a bit off earlier. Everything okay?")

                # existing routine suggestions...
                if mem.is_routine_time("check_agenda"):
                    speak("Kyan, around this time you usually check your agenda. Want me to read it?")
                if mem.is_routine_time("send_text"):
                    speak("Kyan, around this time you usually send a text. Want to send a text?")
                if mem.is_routine_time("start_planning"):
                    speak("Kyan, around this time you start planning. Want to plan something?")
                if mem.is_routine_time("check_train"):
                    speak("You usually check your train around now. Want me to check if it's delayed?")

                # NEW: autonomous engine
                auto.autonomous_check(vision.camera_control.last_interaction_time, emotion=None)  # you can pass last emotion if you track it here
                camera_autonomous_check()
            time.sleep(0.01)
            continue



        # --- TRANSCRIBE ---
        text = transcribe(audio_file)
        emotion = detect_emotion(audio_file)
        is_user = is_kyan(audio_file)

        if text is None or text.strip() == "":
            print("No usable speech detected, retrying...")
            continue

        print("\nYou said:", text)
        gui_main.ui.add_message("Kyan:", text)

        # --- SEND TO BRAIN ---
        response = process_text(text, emotion=emotion, is_user=is_user)
        vision.camera_control.last_interaction_time = time.time()
        gui_main.ui.add_message("Jarvis:", response)

        # If brain returns None → nothing to say
        if not response:
            continue

        # --- SPEAK RESPONSE ---
        speak(response)

if __name__ == "__main__":
    main()
