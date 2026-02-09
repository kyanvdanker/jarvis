# Agenda helper functions
import datetime
import os
import customtkinter

agenda_directory = "/agenda"
agenda_status = {
    "current_date": None
}

def speak(text):
    print(text)

def plan_event(event: str, date: str):
    try:
        event_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        speak("Invalid date format. Please use YYYY-MM-DD.")
        return

    filename = f"{agenda_directory}/{event_date}.txt"
    with open(filename, "a") as f:
        f.write(f"- {event}\n")
    speak(f"Event '{event}' planned for {event_date}")

def view_events(date: str):
    try:
        event_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        speak("Invalid date format. Please use YYYY-MM-DD.")
        return

    filename = f"{agenda_directory}/{event_date}.txt"
    if os.path.isfile(filename):
        speak(f"Events for {event_date}:")
        with open(filename, "r") as f:
            events = f.readlines()
            for event in events:
                speak(event.strip())
    else:
        speak(f"No events found for {event_date}.")

def briefing(date = datetime.date.today().strftime("%Y-%m-%d")):
    try:
        event_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        speak("Invalid date format. Please use YYYY-MM-DD.")
        return

    filename = f"{agenda_directory}/{event_date}.txt"
    if os.path.isfile(filename):
        speak(f"Briefing for {event_date}:")
        with open(filename, "r") as f:
            events = f.readlines()
            if events:
                for event in events:
                    speak(event.strip())
            else:
                speak("No events scheduled.")
    else:
        speak(f"No events found for {event_date}.")

def show_agenda():
    today = datetime.date.today()
    speak("Upcoming events:")
    for i in range(7):  # Show events for the next 7 days
        date = today + datetime.timedelta(days=i)
        filename = f"{agenda_directory}/{date}.txt"
        if os.path.isfile(filename):
            speak(f"{date}:")
            with open(filename, "r") as f:
                events = f.readlines()
                for event in events:
                    speak(f"  - {event.strip()}")
    # Shows events in a a nice GUI format
    root = customtkinter.CTk()
    root.title("Agenda")
    root.geometry("400x600")
    for i in range(7):
        date = today + datetime.timedelta(days=i)
        filename = f"{agenda_directory}/{date}.txt"
        if os.path.isfile(filename):
            label = customtkinter.CTkLabel(root, text=f"{date}:", font=("Arial", 16, "bold"))
            label.pack(pady=(10, 0))
            with open(filename, "r") as f:
                events = f.readlines()
                for event in events:
                    event_label = customtkinter.CTkLabel(root, text=f"  - {event.strip()}", font=("Arial", 14))
                    event_label.pack(anchor="w", padx=20)
    root.mainloop()

def reminder(event: str, date: str):
    try:
        event_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        speak("Invalid date format. Please use YYYY-MM-DD.")
        return

    filename = f"{agenda_directory}/{event_date}.txt"
    with open(filename, "a") as f:
        f.write(f"- Reminder: {event}\n")
    speak(f"Reminder for '{event}' set for {event_date}")
