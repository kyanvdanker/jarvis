import re
import uuid
from datetime import datetime, timedelta
import os
import csv
import difflib
import threading
import time
from speak import speak
from intent_classifier.intent_classifier import classify_intent_ml
from cad_dialog import start_cad_creation, continue_cad_dialog, modify_last_part
import cad_dialog
from cad_intent import detect_cad_component, wants_creation
from simulation_dialog import (
    start_simulation_dialog,
    continue_simulation_dialog
)
import simulation_dialog
from project_manager import (
    create_project,
    switch_project,
    list_projects,
    add_note,
    read_notes,
    ROOT_DIR,
    project_exists,
    add_requirement, 
    list_requirements, 
    add_material, 
    list_materials, 
    add_decision, 
    list_decisions
)
import project_manager
from calander_manager import (
    get_todays_events,
    get_briefing,
    start_planning,
    continue_planning,
    save_wake_time
)
import calander_manager
from printer import send_to_printer
from gui_viewer import rotate_camera, zoom_camera, reset_camera, start_viewer, close_viewer, load_stl_into_viewer
from vision.camera_control import start_gesture_camera
from ollama_client import stream_ollama
from word2number import w2n
from helpers import ReminderManager, REMINDER_FILE
import helpers
import webbrowser
import time
import pyautogui
import webbrowser
import memory_manager as mem
from check_ns import check_train_delay
from gui_main import open_file_in_gui, update_timeline, update_memory
import autonymous as auto
import vision.camera_control
from autonomous_reasoning.llm_reasoner import proactive_review
import memory

autonomy_state = {
    "last_suggestion": None,
    "waiting_for_confirmation": False
}

CONTACTS = {
    "mom": "+31636191234"
}

wake_state = {
    "active": False,
    "stage": None,
    "time": None
}

call_state = {
    "active": False,
    "stage": None,
    "number": None
}

whatsapp_state = {
    "active": False,
    "stage": None,
    "number": None,
    "message": None
}

emotion_state = {
    "last": "neutral",
    "history": []
}

speaker_state = {
    "last_is_user": True
}

personality_state = {
    "mode": "neutral",   # "calm", "energetic", "concise", "supportive"
}

emotion_state = {
    "last": "neutral",
    "baseline": "neutral",
    "history": []
}

security_state = False

speaker_state = {
    "last_is_user": True,
    "security_level": 2  # 1=anyone, 2=only you for commands, 3=you for sensitive
}

habit_state = {
    "last_actions": [],      # recent intents
    "predictions_enabled": True
}

health_state = {
    "stress_score": 0.0,
    "fatigue_score": 0.0,
    "last_check": None
}

last_interaction_time = None
# ---------- GLOBAL STATE FOR BRAIN ----------

conversation_history = []
MAX_HISTORY = 10

last_suggestions = []
pending_sentence = None
suggestion_mode = False
reasoning_mode = False

reasoning_state = {
    "active": False
}

project_state = {
    "active": False,
    "mode": None,       # "create", "switch", "add_note"
    "pending_name": "",
}

# ---------- SMALL HELPERS (TEXT / NUMBERS / HISTORY) ----------

reminder_manager = ReminderManager(speak)

def resolve_contact(name: str):
    name = name.lower().strip()
    if name in CONTACTS:
        return CONTACTS[name]
    return None

def speak_with_personality(text):
    mode = personality_state["mode"]
    if mode == "concise":
        # maybe shorten text later; for now just speak_with_personality
        speak(text)
    elif mode == "supportive":
        speak(text + " If you want, I can make things easier or slower.")
    elif mode == "energetic":
        speak(text)
    else:
        speak(text)

def clean_text_for_classification(text: str) -> str:
    if text is None:
        return ""
    return re.sub(r'[^a-zA-Z0-9\s]', '', text).lower()

def start_security_dialog():
    global security_state
    security_state = True
    speak_with_personality("Sure what should the security level be?")
    time.sleep(4)

def continue_security_dialog(text):
    global security_state
    level = text.strip()
    if not level:
        speak_with_personality("I didn't catch the level. What should the level be?")
        time.sleep(5)
        return
    
    speaker_state["security_level"] = level
    speak_with_personality("Level is set to", level)

    security_state = False


def start_create_project_dialog():
    project_state["active"] = True
    project_state["mode"] = "create"
    speak_with_personality("Sure — what should I name the new project?")
    time.sleep(4)

def continue_create_project_dialog(text):
    name = text.strip()
    if not name:
        speak_with_personality("I didn't catch the name. What should the project be called?")
        time.sleep(5)
        return

    result = create_project(name)
    speak_with_personality(result)

    # reset
    project_state["active"] = False
    project_state["mode"] = None


def start_switch_project_dialog():
    project_state["active"] = True
    project_state["mode"] = "switch"
    speak_with_personality("Which project would you like to switch to?")
    time.sleep(3)

def continue_switch_project_dialog(text):
    name = text.strip()
    if not name:
        speak_with_personality("Please tell me the project name.")
        time.sleep(3)
        return

    result = switch_project(name)
    speak_with_personality(result)

    # reset
    project_state["active"] = False
    project_state["mode"] = None

def update_health_from_emotion(emotion):
    if emotion in ["angry", "stressed"]:
        health_state["stress_score"] += 0.2
    elif emotion in ["sad", "tired"]:
        health_state["fatigue_score"] += 0.2
    else:
        health_state["stress_score"] *= 0.9
        health_state["fatigue_score"] *= 0.9

    health_state["stress_score"] = min(1.0, health_state["stress_score"])
    health_state["fatigue_score"] = min(1.0, health_state["fatigue_score"])

def maybe_comment_on_health():
    if health_state["stress_score"] > 0.7:
        speak_with_personality("Your voice sounds pretty tense lately. Have you been under a lot of stress?")
    elif health_state["fatigue_score"] > 0.7:
        speak_with_personality("You sound tired. Maybe a short break or some water would help.")

def start_whatsapp_dialog():
    whatsapp_state["active"] = True
    whatsapp_state["stage"] = "ask_number"
    speak_with_personality("Sure — who should I message? You can say a name or a phone number.")
    time.sleep(6)

def continue_whatsapp_dialog(text):
    if whatsapp_state["stage"] == "ask_number":
        raw = text.strip()
        number = resolve_contact(raw)

        if number is None:
            # assume user gave a number
            number = raw

        whatsapp_state["number"] = number
        whatsapp_state["stage"] = "ask_message"
        speak_with_personality("What message should I send?")
        time.sleep(3)
        return


    if whatsapp_state["stage"] == "ask_message":
        whatsapp_state["message"] = text.strip()
        whatsapp_state["stage"] = "confirm"
        speak_with_personality(f"Do you want me to send this message to {whatsapp_state['number']}: '{whatsapp_state['message']}'?")
        time.sleep(6)
        return

    if whatsapp_state["stage"] == "confirm":
        if "yes" in text.lower():
            send_whatsapp(whatsapp_state["number"], whatsapp_state["message"])
            speak_with_personality("Message sent.")
        else:
            speak_with_personality("Okay, I won't send it.")

        # reset
        whatsapp_state["active"] = False
        whatsapp_state["stage"] = None
        whatsapp_state["number"] = None
        whatsapp_state["message"] = None

def start_add_note_dialog():
    project_state["active"] = True
    project_state["mode"] = "add_note"
    speak_with_personality("What note would you like to add?")
    time.sleep(3)

def continue_add_note_dialog(text):
    note = text.strip()
    if not note:
        speak_with_personality("Please tell me the note you want to add.")
        time.sleep(4)
        return

    result = add_note(note)
    speak_with_personality(result)

    # reset
    project_state["active"] = False
    project_state["mode"] = None

def log_intent(intent):
    habit_state["last_actions"].append({
        "intent": intent,
        "time": datetime.now().isoformat()
    })
    if len(habit_state["last_actions"]) > 100:
        habit_state["last_actions"].pop(0)

def predict_next_intent():
    if len(habit_state["last_actions"]) < 5:
        return None
    last = habit_state["last_actions"][-1]["intent"]
    # naive: if same last intent appears often, suggest continuing
    count = sum(1 for a in habit_state["last_actions"] if a["intent"] == last)
    if count >= 3:
        return last
    return None


def convert_words_to_numbers(text: str) -> str:
    try:
        words = text.split()
        for i, word in enumerate(words):
            try:
                num = w2n.word_to_num(word)
                words[i] = str(num)
            except Exception:
                pass
        return " ".join(words)
    except Exception:
        return text
    
def send_whatsapp(contact_number, message):
    webbrowser.open(f"https://web.whatsapp.com/send?phone={contact_number}")
    time.sleep(8)  # wait for WhatsApp Web to load
    pyautogui.typewrite(message)
    pyautogui.press("enter")

def add_to_history(role, text):
    global conversation_history
    conversation_history.append({"role": role, "text": text})
    if len(conversation_history) > MAX_HISTORY:
        conversation_history.pop(0)


def build_history_text():
    return "\n".join([f"{h['role']}: {h['text']}" for h in conversation_history])

def build_memory():
    mem_items = []

    stress, fatigue = mem.get_health()
    mem_items.append(f"Stress: {stress:.2f}")
    mem_items.append(f"Fatigue: {fatigue:.2f}")

    if helpers.speaker_verified:
        mem_items.append("Speaker: Kyan")
    else:
        mem_items.append("Speaker: Unknown")

    if helpers.emotion_learning_state["active"]:
        mem_items.append("Emotion learning: ON")

    return mem_items

def ask_ollama_stream(prompt: str, model: str = "llama3"):
    try:
        buffer = ""
        for token in stream_ollama(prompt, model=model):
            buffer += token
            if len(buffer) > 45 or any(p in token for p in ".,!?;:"):
                speak_with_personality(buffer.strip())
                buffer = ""
        if buffer:
            speak_with_personality(buffer.strip())
    except Exception as e:
        print("Streaming error:", e)
        speak_with_personality("There was an error streaming the response.")


# ---------- VIEW COMMANDS (SIDE EFFECT ONLY) ----------

def handle_view_commands(text):
    t = text.lower()

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

    if "zoom in" in t:
        zoom_camera(0.9)
        return True
    if "zoom out" in t:
        zoom_camera(1.1)
        return True

    if "reset view" in t or "reset camera" in t:
        reset_camera()
        return True

    return False


# ---------- REMINDER PARSING (DIRECT ONE-SHOT) ----------

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


# ---------- PRINTING HELPERS ----------

def extract_print_target(text):
    return text.lower().replace("print", "").strip()


def find_best_matching_file(name):
    if project_manager.current_project is None:
        return None, "No project selected."

    project_path = os.path.join(ROOT_DIR, project_manager.current_project)
    files = [f for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f))]
    match = difflib.get_close_matches(name, files, n=1, cutoff=0.3)
    if not match:
        return None, "No matching file found."
    return os.path.join(project_path, match[0]), None

def place_call(number):
    url = f"tel://{number}"
    webbrowser.open(url)

# ---------- SUGGESTION SELF-LEARNING ----------

def add_training_example(sentence, intent):
    os.makedirs("intent_classifier", exist_ok=True)
    path = os.path.join("intent_classifier", "intent_data.csv")
    new_file = not os.path.exists(path)

    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["sentence", "intent"])
        writer.writerow([sentence, intent])

def build_timeline():
    lines = []

    # Reminders
    for r in reminder_manager.reminders:
        t = datetime.fromisoformat(r["trigger_time"])
        status = "✓" if r["triggered"] == "1" else "•"
        lines.append(f"{t.strftime('%H:%M')}  {status}  {r['message']}")

    # Planning suggestions
    if calander_manager.planning_state["active"]:
        lines.append("\nPlanning in progress…")

    # Routines
    for name, times in mem._load().get("routine", {}).items():
        avg = sum([t["hour"]*60 + t["minute"] for t in times]) / len(times)
        h = int(avg // 60)
        m = int(avg % 60)
        lines.append(f"{h:02d}:{m:02d}  Routine: {name}")

    return "\n".join(lines)


def start_reminder_dialog():
    helpers.reminder_state["active"] = True
    helpers.reminder_state["stage"] = "what"
    speak_with_personality("Sure, what would you like me to remind you about?")

def start_call_dialog():
    call_state["active"] = True
    call_state["stage"] = "ask_number"
    speak_with_personality("Who would you like to call? Tell me the phone number.")

def continue_call_dialog(text):
    if call_state["stage"] == "ask_number":
        call_state["number"] = text.strip()
        call_state["stage"] = "confirm"
        speak_with_personality(f"Do you want me to call {call_state['number']} now?")
        return

    if call_state["stage"] == "confirm":
        if "yes" in text.lower():
            place_call(call_state["number"])
            speak_with_personality("Calling now.")
        else:
            speak_with_personality("Okay, I won't call.")
        
        # reset
        call_state["active"] = False
        call_state["stage"] = None
        call_state["number"] = None

def parse_wake_time(text):
    # Match: wake me at 7, wake me at 10, wake me at 0, etc.
    m = re.search(r"(\d{1,2})", text)
    if not m:
        return None

    hour = int(m.group(1))

    # Interpret 0–12 as AM
    if 0 <= hour <= 12:
        pass  # already AM

    # Interpret 13–23 as PM (24h format)
    elif 13 <= hour <= 23:
        pass

    else:
        return None

    now = datetime.now()
    wake = now.replace(hour=hour, minute=0, second=0, microsecond=0)

    # If the time already passed today → schedule for tomorrow
    if wake < now:
        wake += timedelta(days=1)

    return wake

def continue_reminder_dialog(text):
    if helpers.reminder_state["stage"] == "what":
        helpers.reminder_state["message"] = text.strip()
        helpers.reminder_state["stage"] = "when"
        speak_with_personality(f"Got it — remind you about '{text}'. When should I remind you? "
              "Say something like 'in 30 minutes' or 'at 3:45'.")

    elif helpers.reminder_state["stage"] == "when":
        parsed = parse_reminder_command(text)
        if parsed:
            kind, value, _ = parsed
            if kind == "in":
                trigger = datetime.now() + timedelta(minutes=value)
            else:  # "at"
                trigger = value

            helpers.reminder_state["trigger"] = trigger

            # Actually set the reminder
            reminder_manager.add_at(trigger, helpers.reminder_state["message"])
            
            time_str = trigger.strftime("%H:%M %p on %A")
            speak_with_personality(f"Reminder set! I'll remind you about '{helpers.reminder_state['message']}' "
                  f"at {time_str}.")

            # Reset state
            helpers.reminder_state["active"] = False
            helpers.reminder_state["stage"] = None
            helpers.reminder_state["message"] = ""
            helpers.reminder_state["trigger"] = None

def execute_autonomous_action(suggestion):
    if "wake-up" in suggestion:
        speak("What time should I wake you?")
        wake_state["active"] = True
        wake_state["stage"] = "ask_time"
        return None

    if "agenda" in suggestion:
        return get_todays_events()

    if "break" in suggestion:
        speak("Alright. I’ll remind you to stretch in 10 minutes.")
        reminder_manager.add_in(10, "Take a short break")
        return None

    return "Done."


def update_personality_from_emotion(emotion):
    if emotion in ["angry", "frustrated"]:
        personality_state["mode"] = "concise"
    elif emotion in ["sad", "tired"]:
        personality_state["mode"] = "supportive"
    elif emotion in ["happy", "excited"]:
        personality_state["mode"] = "energetic"
    else:
        personality_state["mode"] = "neutral"

# ---------- MAIN BRAIN ENTRYPOINT ----------

def process_text(raw_text: str, emotion=None, is_user=True) -> str | None:
    global last_suggestions, pending_sentence, suggestion_mode
    global last_interaction_time, security_state
    update_memory(build_memory())
    update_timeline(build_timeline())

    last_interaction_time = datetime.now()

    if raw_text is None:
        return None
        # --- AUTONOMOUS SUGGESTION CONFIRMATION ---
    resp = auto.handle_autonomy_response(raw_text)
    if resp is not None:
        return resp

    # Clean + normalize
    clean = clean_text_for_classification(raw_text)
    clean = convert_words_to_numbers(clean)

    SENSITIVE_INTENTS = {"send_whatsapp", "call_start", "print", "delete_project"}

    if not is_user:
        if vision.camera_control.camera_verified_user:
            is_user = True  # override with camera identity
        else:
            if speaker_state["security_level"] >= 2:
                speak("This doesn't sound like you. I won't execute commands unless you confirm.")
                helpers.speaker_check_state = True
                return None


    if helpers.speaker_check_state:
        if "yes" in raw_text.lower():
            speak("Okay, I'll accept commands from this voice for now.")
        else:
            speak("Alright, I'll ignore commands from this voice.")
            return None
        helpers.speaker_check_state = False


    if not is_user:
        speak_with_personality("This doesn't sound like you. Should I respond?")
        helpers.speaker_check_state = True
        return None

    if helpers.speaker_check_state:
        if "yes" in raw_text.lower():
            speak_with_personality("Okay, I'll respond.")
        else:
            speak_with_personality("Alright, ignoring the command.")
            helpers.speak_with_personalityer_check_state = False
            return None
        helpers.speak_with_personalityer_check_state = False


    if emotion:
        emotion_state["history"].append(emotion)
        if len(emotion_state["history"]) > 20:
            emotion_state["history"].pop(0)

        previous = emotion_state["last"]
        emotion_state["last"] = emotion

    if emotion and emotion != previous:
        speak_with_personality(f"Kyan, you sound {emotion}. Is that correct?")
        helpers.emotion_learning_state = {
            "active": True,
            "detected": emotion
        }
        return None
    
        # --- EMOTION + MEMORY INTEGRATION ---
    previous_emotion = emotion_state["last"]

    if emotion:
        emotion_state["last"] = emotion
        mem.log_emotion(emotion)

        # simple health update
        if emotion in ["angry", "frustrated", "stressed"]:
            stress, fatigue = mem.update_health(stress_delta=0.1)
        elif emotion in ["sad", "tired"]:
            stress, fatigue = mem.update_health(fatigue_delta=0.1)
        else:
            # decay
            stress, fatigue = mem.update_health(stress_delta=-0.05, fatigue_delta=-0.05)

        # gentle ambient health comments
        if stress > 0.7:
            speak("You’ve sounded pretty tense lately. Maybe a short break would help.")
        elif fatigue > 0.7:
            speak("You sound tired. Consider a quick pause or some water.")

        # optional: detect big deviation from baseline
        baseline = mem.get_baseline_emotion()
        if previous_emotion != "neutral" and baseline == "neutral":
            mem.set_baseline_emotion(previous_emotion)

    
    if emotion:
        previous = emotion_state["last"]
        emotion_state["last"] = emotion
        emotion_state["history"].append(emotion)
        if len(emotion_state["history"]) > 50:
            emotion_state["history"].pop(0)

        update_personality_from_emotion(emotion)

    if emotion:
        update_health_from_emotion(emotion)
        maybe_comment_on_health()

    if helpers.emotion_learning_state["active"]:
        if "yes" in raw_text.lower():
            # Confirmed emotion
            confirmed = helpers.emotion_learning_state["detected"]
            # Save training example
            with open("emotion_training.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([raw_text, confirmed])
            speak_with_personality("Thanks, I’ll remember that.")
        else:
            speak_with_personality("Okay, I won’t record that emotion.")

        helpers.emotion_learning_state["active"] = False
        return None


    if not clean.strip():
        return None

    # ---------- DIALOG FOLLOW-UPS OVERRIDE EVERYTHING ----------

    # ---------- REASONING MODE TOGGLE ----------
    lower = raw_text.lower()

    # Enter reasoning mode
    if any(phrase in lower for phrase in [
        "let's brainstorm",
        "lets brainstorm",
        "let's think",
        "lets think",
        "help me think",
        "reason with me",
        "switch to reasoning mode",
        "enter reasoning mode",
        "let's analyze this"
    ]):
        reasoning_state["active"] = True
        speak("Alright, switching to reasoning mode. I’ll focus only on analysis and ideas.")
        return None

    # Exit reasoning mode
    if any(phrase in lower for phrase in [
        "go back to normal",
        "normal mode",
        "stop brainstorming",
        "stop reasoning",
        "exit reasoning mode",
        "return to normal"
    ]):
        reasoning_state["active"] = False
        speak("Okay, back to normal mode.")
        return None

    # If in reasoning mode → only do LLM reasoning
    if reasoning_state["active"]:
        result = proactive_review(raw_text, project_name=None)
        if result:
            speak(result)
        else:
            speak("I'm thinking about it, but I don't see anything important yet.")
        return None

    # CAD dialog
    if cad_dialog.cad_state.get("active"):
        continue_cad_dialog(clean)
        return None
    
    if autonomy_state["waiting_for_confirmation"]:
        t = clean

        if "yes" in t or "sure" in t or "okay" in t:
            suggestion = autonomy_state["last_suggestion"]
            if suggestion == "switch_to_reasoning":
                reasoning_state["active"] = True
                speak("Okay, switching to reasoning mode.")
                return None

            autonomy_state["waiting_for_confirmation"] = False

            return execute_autonomous_action(suggestion)

        if "no" in t or "not now" in t:
            autonomy_state["waiting_for_confirmation"] = False
            return "Alright."

        # If unclear, ask again
        return "Should I do that?"

    
    # --- Project dialogs ---
    if project_state["active"]:
        mode = project_state["mode"]
        if mode == "create":
            continue_create_project_dialog(clean)
            return None
        if mode == "switch":
            continue_switch_project_dialog(clean)
            return None
        if mode == "add_note":
            continue_add_note_dialog(clean)
            return None
        if mode == "add_requirement":
            result = add_requirement(clean)
            speak(result)
            project_state["active"] = False
            project_state["mode"] = None
            return None       
        if mode == "add_decision":
            result = add_decision(clean)
            speak(result)
            project_state["active"] = False
            project_state["mode"] = None
            return None
        if mode == "add_material":
            result = add_material(clean)
            speak(result)
            project_state["active"] = False
            project_state["mode"] = None
            return None


    # Simulation dialog
    if simulation_dialog.simulation_state.get("active"):
        continue_simulation_dialog(clean)
        return None

    # Planning dialog
    if calander_manager.planning_state.get("active"):
        continue_planning(clean)
        return None
    
    # --- Reminders (multi-step dialog) ---
    if helpers.reminder_state["active"]:
        # Continue the multi-step dialog
        continue_reminder_dialog(clean)
        return None
    
    if whatsapp_state["active"]:
        continue_whatsapp_dialog(clean)
        return None
    
    if security_state:
        continue_security_dialog(clean)
        return None

    
    if call_state["active"]:
        continue_call_dialog(clean)
        return None
    
    if wake_state["active"]:
        if wake_state["stage"] == "ask_time":
            try:
                t = parse_wake_time(clean)
                wake_state["time"] = t
                save_wake_time(t)
                speak(f"Okay, I will wake you at {t.strftime('%H:%M')}.")
                wake_state["active"] = False
                wake_state["stage"] = None
            except:
                speak("I couldn't understand the time. Please say it again.")
            return None


    # Reminders dialog (multi-step)
    # reminder_state is managed in your other module; here we just call follow-up
    # if it's active, but we don't have direct access here, so we rely on intent instead.

    # ---------- VIEW COMMANDS (NO INTENT NEEDED) ----------
    if handle_view_commands(clean):
        return None
    
    next_guess = predict_next_intent()
    if next_guess and next_guess in {"cad_start", "simulate_motor", "open_file"}:
        speak_with_personality(f"Do you want to continue with {next_guess.replace('_', ' ')} like before?")


    # ---------- SUGGESTION MODE ANSWER ----------
    if suggestion_mode and last_suggestions:
        t = clean.lower()
        if any(phrase in t for phrase in ["yes", "yeah", "that", "correct", "the first", "first one", "second", "third"]):
            # Determine which suggestion user meant
            choice = None
            if any(x in t for x in ["first", "1st", "one", "1"]):
                choice = last_suggestions[0]
            elif any(x in t for x in ["second", "2nd", "two", "2"]):
                choice = last_suggestions[1] if len(last_suggestions) > 1 else last_suggestions[0]
            elif any(x in t for x in ["third", "3rd", "three", "3"]):
                choice = last_suggestions[2] if len(last_suggestions) > 2 else last_suggestions[0]
            else:
                choice = last_suggestions[0]

            # Self-learning
            if pending_sentence:
                add_training_example(pending_sentence, choice)
                pending_sentence = None

            # Clear suggestion mode
            suggestion_mode = False
            last_suggestions = []

            

            # Re-run as if user said the canonical phrase
            clean = clean_text_for_classification(choice)
            # fall through to intent handling with this simulated intent
            intent = choice
            confidence = 1.0
        else:
            # User said something else while in suggestion mode → treat as fresh input
            suggestion_mode = False
            last_suggestions = []
            intent, confidence, ranked = classify_intent_ml(clean)
    else:
        # ---------- NORMAL INTENT CLASSIFICATION ----------
        intent, confidence, ranked = classify_intent_ml(clean)

    # ---------- LOW CONFIDENCE → SUGGESTION ----------
    if confidence < 0.25:
        if ranked:
            suggestions = [i for i, p in ranked[:3]]
            if len(suggestions) < 3:
                # pad if needed
                while len(suggestions) < 3:
                    suggestions.append(suggestions[-1])
            last_suggestions = suggestions
            pending_sentence = clean
            suggestion_mode = True
            return f"I'm not sure. Did you mean {suggestions[0]}, {suggestions[1]}, or {suggestions[2]}?"
        else:
            return "I'm not sure what you meant."

    # If we got here without setting intent (only in suggestion branch above)
    if "intent" not in locals():
        intent = intent

    # ---------- HANDLE INTENTS ----------

    if intent in SENSITIVE_INTENTS and speaker_state["security_level"] == 3 and not is_user:
        return "This action requires your voice, Kyan."

    if "intent" in locals():
        mem.log_intent(intent)

    if "intent" in locals():
        mem.log_intent(intent)
        predicted = mem.predict_next_intent()
        if predicted and predicted != intent:
            speak(f"Do you want to continue with {predicted.replace('_', ' ')} like before?")

    # --- Call dialog ---
    if intent == "call_start":
        start_call_dialog()
        return None
    
    if intent == "wake_start":
        wake_state["active"] = True
        wake_state["stage"] = "ask_time"
        speak("Sure, what time should I wake you?")
        return None

    # --- Remember something ---
    if intent == "remember":
        # Extract a number or phrase from the text
        m = re.search(r"(\d+)", clean)
        if m:
            value = int(m.group(1))
        else:
            # fallback: remember the whole cleaned text after the word "remember"
            parts = clean.split("remember", 1)
            value = parts[1].strip() if len(parts) > 1 else clean

        memory.remember_value(value)
        return f"Okay, I’ll remember {value}."

    # --- Recall remembered value ---
    if intent == "recall":
        value = memory.recall_value()
        if value is None:
            return "You haven't asked me to remember anything yet."
        return f"You told me to remember {value}."

    # --- WhatsApp dialog ---
    if intent == "whatsapp_start":
        mem.log_routine_event("send_text")
        start_whatsapp_dialog()
        return None
    
    if intent == "security_start":
        start_security_dialog()
    
    # View already handled above, but keep for safety
    if intent == "view":
        handle_view_commands(clean)
        return None
    
    if intent == "list_requirements":
        reqs = list_requirements()
        if not reqs:
            return "No requirements yet."
        return "\n".join([f"- {r['text']}" for r in reqs])

    if intent == "list_materials":
        mats = list_materials()
        if not mats:
            return "No materials recorded."
        return "\n".join([f"- {m['material']}" for m in mats])
    
    if intent == "list_decisions":
        decs = list_decisions()
        if not decs:
            return "No design decisions yet."
        return "\n".join([f"- {d['description']}" for d in decs])


    if intent == "add_decision":
        speak("What design decision should I record?")
        project_state["active"] = True
        project_state["mode"] = "add_decision"
        return None

    # --- Simulation ---
    if intent == "simulate_motor":
        start_simulation_dialog()
        return "Starting motor simulation. What is the outer radius in millimeters?"

    if intent == "simulation_followup":
        continue_simulation_dialog(clean)
        return None
    
    # --- Projects / Notes (multi-step) ---
    if intent == "create_project":
        start_create_project_dialog()
        return None

    if intent == "switch_project":
        start_switch_project_dialog()
        return None

    if intent == "add_note":
        start_add_note_dialog()
        return None


    # --- CAD ---
    if intent == "cad_start":
        # Start viewer + gesture camera (local use)
        try:
            # These are side effects; if running on server you can guard them
            import threading
            threading.Thread(target=start_viewer, daemon=True).start()
            threading.Thread(target=start_gesture_camera, daemon=True).start()
        except Exception as e:
            print("Viewer/camera start error:", e)

        component_name = detect_cad_component(clean)
        dry_run = "dry" in clean.lower()
        start_cad_creation(component_name, dry_run)
        return None

    if intent == "cad_followup":
        continue_cad_dialog(clean)
        return None

    if intent == "cad_modify":
        modify_last_part(clean)
        return None
    


    # Direct one-shot reminder: "remind me in 10 minutes"
    if intent == "reminder":
        parsed = parse_reminder_command(clean)
        if parsed:
            kind, value, original = parsed

            if kind == "in":
                reminder_manager.add_in(value, original)
                return f"Okay, I'll remind you in {value} minutes."

            if kind == "at":
                reminder_manager.add_at(value, original)
                when_str = value.strftime('%H:%M')
                return f"Okay, I'll remind you at {when_str}."

        # If parsing failed → fall back to multi-step dialog
        start_reminder_dialog()
        return None

    # Start multi-step reminder dialog: "set a reminder"
    if intent == "reminder_start":
        start_reminder_dialog()
        return None

    # Follow-up step: "reminder_followup"
    if intent == "reminder_followup":
        continue_reminder_dialog(clean)
        return None
    
    if intent == "open_cad_viewer":
        helpers.UI_STATE = "cad"
        start_viewer()
        speak_with_personality("Opening the CAD viewer.")
        return None

    if intent == "close_cad_viewer":
        helpers.UI_STATE = "main"
        close_viewer()
        speak_with_personality("Closing the CAD viewer.")
        return None

    if intent == "add_requirement":
        speak("What requirement should I add?")
        project_state["active"] = True
        project_state["mode"] = "add_requirement"
        return None

    if intent == "add_material":
        speak("Which material should I add?")
        project_state["active"] = True
        project_state["mode"] = "add_material"
        return None


    if intent == "read_notes":
        return read_notes()

    # --- Agenda / Briefing ---
    if intent == "agenda_today":
        mem.log_routine_event("check_agenda")
        return get_todays_events()

    if intent == "briefing":
        # your get_briefing already builds a full sentence
        return get_briefing()
    
    if intent == "check_train":
    # You can hardcode your route or ask in dialog
        mem.log_routine_event("check_train")

        result = check_train_delay("Cl", "Ehv", datetime.now())

        if not result:
            return "I couldn't find your train."

        if result["delay"] and result["delay"] > 0:
            minutes = result["delay"] // 60
            return f"Your train is delayed by {minutes} minutes."
        else:
            return "Your train is on time."


    # --- Planning ---
    if intent == "planning_start":
        mem.log_routine_event("start_planning")
        start_planning(clean)
        return None

    if intent == "planning_followup":
        continue_planning(clean)
        return None
    
    if intent == "open_file":
        speak_with_personality("Which file would you like to open?")
        helpers.project_state["active"] = True
        helpers.project_state["mode"] = "open_file"
        return None

    if helpers.project_state["active"] and helpers.project_state["mode"] == "open_file":
        path, err = find_best_matching_file(clean)
        if err:
            speak_with_personality(err)
        else:
            speak_with_personality(f"Opening {os.path.basename(path)}.")
            open_file_in_gui(path)
              # Windows only
        helpers.project_state["active"] = False
        helpers.project_state["mode"] = None
        return None


    # --- Printing ---
    if intent == "print":
        target = extract_print_target(clean)
        stl_path, err = find_best_matching_file(target)
        if err:
            return err

        speak_with_personality(f"Printing {target}.")
        result = send_to_printer(stl_path)
        if result is True:
            return "Print started."
        else:
            return "Failed to start print."

    # --- Questions (Ollama) ---
    if intent == "question":
        history_text = build_history_text()
        prompt = f"{history_text}\nUser: {raw_text}"
        add_to_history("User", raw_text)
        ask_ollama_stream(prompt)
        add_to_history("Jarvis", "(streamed response)")
        return None

    # --- Fallback ---
    return "Sorry, I don't understand that."
