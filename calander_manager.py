import win32com.client
from datetime import datetime, timedelta
import requests
from speak import speak
from project_manager import read_notes, create_project, current_project, add_note
import logging
import time
import json
from dateutil import parser
import os

planning_state = {
    "active": False,
    "stage": None,
    "details": {"name": "", "goals": "", "deadline": ""}
}

AGENDA_FILE = "agenda.json"

WAKE_FILE = "wake_time.json"

def save_wake_time(dt):
    with open(WAKE_FILE, "w") as f:
        json.dump({"wake_time": dt.isoformat()}, f)

def load_wake_time():
    if not os.path.exists("wake_time.json"):
        return None

    try:
        with open("wake_time.json", "r") as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except Exception:
        return None


def clear_wake_time():
    if os.path.exists(WAKE_FILE):
        os.remove(WAKE_FILE)

def load_agenda():
    if not os.path.exists(AGENDA_FILE):
        return []
    with open(AGENDA_FILE, "r") as f:
        return json.load(f)

def save_agenda(appointments):
    with open(AGENDA_FILE, "w") as f:
        json.dump(appointments, f, indent=4)

def create_file_deadline_appointment(project_name, deadline_text, goals=""):
    """
    Saves an appointment to agenda.json instead of Outlook.
    """
    try:
        try:
            due_date = parser.parse(deadline_text, fuzzy=True).date()
        except:
            due_date = (datetime.now() + timedelta(days=1)).date()

        appointments = load_agenda()

        appointments.append({
            "project": project_name,
            "date": due_date.isoformat(),
            "goals": goals,
            "deadline_text": deadline_text
        })

        save_agenda(appointments)
        return True
    except Exception as e:
        print("Could not save appointment:", e)
        return False

def get_todays_events():
    appointments = load_agenda()
    if not appointments:
        return "You have no events scheduled for today."

    today = datetime.now().date()
    todays = [a for a in appointments if parser.parse(a["date"]).date() == today]

    if not todays:
        return "You have no events scheduled for today."

    summary = "Here is your schedule for today. "

    for appt in todays:
        summary += f"{appt['project']} — goals: {appt['goals']}. "

    return summary.strip()

WEATHER_API_KEY = "a4fd285f22e5a88262505e546d9068c7"  # Get free from openweathermap.org

def get_briefing(reminder_manager=None):
    # Time
    now = datetime.now()
    time_str = now.strftime("%I:%M %p on %B %d, %Y")  # e.g., "03:31 PM on January 15, 2026"

    # Weather (simple API call)
    try:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q=Zoelmond,NL&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(weather_url).json()
        if response.get("cod") == 200:
            temp = response["main"]["temp"]
            desc = response["weather"][0]["description"]
            weather_str = f"It's currently {temp}°C with {desc} in Zoelmond."
        else:
            weather_str = "Couldn't get weather right now."
    except Exception as e:
        logging.error(f"Weather error: {e}")
        weather_str = "Weather check failed—check your API key?"

    # Events & Reminders
    events = get_todays_events() or "No events today."

    pending_reminders = []
    if reminder_manager is not None:
        pending_reminders = [
            r['message'] 
            for r in reminder_manager.reminders 
            if r['triggered'] == "0"
        ]
    
    reminders_str = f"You have {len(pending_reminders)} pending reminders: " + \
                    (f"{', '.join(pending_reminders[:3])}." if pending_reminders else "none.")
    
    notes = read_notes() or "No notes."

    briefing = f"Good day, Kyan! It's {time_str}. {weather_str} {events} {reminders_str} Recent notes: {notes}"
    return briefing

def start_planning(text):
    planning_state["active"] = True
    
    # NEW: Check if there's a current project
    if current_project:
        # Skip name stage if already in a project
        planning_state["details"]["name"] = current_project
        planning_state["stage"] = "goals"
        speak(f"Planning for existing project '{current_project}'. What are the main goals?")
        time.sleep(4)
    else:
        # No current project → ask for name and plan to create
        planning_state["stage"] = "name"
        speak("Starting project planning. What's the project name?")
        time.sleep(5)

def continue_planning(text):
    if planning_state["stage"] == "name":
        if current_project != project_name:  # Means we asked for name → new project
            speak("This project does not exist.")
            return
        planning_state["details"]["name"] = text.strip()
        planning_state["stage"] = "goals"
        speak(f"Got name '{planning_state['details']['name']}'. What are the main goals?")
        time.sleep(5)
    elif planning_state["stage"] == "goals":
        planning_state["details"]["goals"] = text.strip()
        planning_state["stage"] = "deadline"
        speak("Goals noted. What's the deadline? Say like 'next Friday'.")
        time.sleep(5)
    elif planning_state["stage"] == "deadline":
        planning_state["details"]["deadline"] = text.strip()
        
        # NEW: Only create new project if no current one (and name was asked)
        project_name = planning_state["details"]["name"]
        
        # Add note (works for both new and existing)
        note_text = f"Goals: {planning_state['details']['goals']}. Deadline: {planning_state['details']['deadline']}."
        add_note(note_text)
        
        # NEW: Create Outlook deadline event (from previous suggestion – assuming you added it)
        success = create_file_deadline_appointment(
            project_name,
            planning_state["details"]["deadline"],
            planning_state["details"]["goals"]
        )

        
        if success:
            speak(f"Project '{project_name}' planned! Goals and deadline saved. I added it to your agenda file.")
        else:
            speak(f"Project '{project_name}' planned, but I couldn't save the agenda entry.")

                
        planning_state["active"] = False  # Reset