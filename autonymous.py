# autonomous_engine.py

from datetime import datetime, timedelta
import memory_manager as mem
import helpers
from speak import speak
import time

autonomy_state = {
    "waiting_for_confirmation": False,
    "last_suggestion": None,
    "last_suggestion_key": None,
    "last_suggestion_time": None,
    "cooldowns": {},   # key -> datetime
}

# seconds before we can suggest same thing again
DEFAULT_COOLDOWN = 60 * 60   # 10 minutes


def _on_cooldown(key: str) -> bool:
    now_dt = datetime.now()
    t = autonomy_state["cooldowns"].get(key)
    return t is not None and now_dt < t


def _set_cooldown(key: str, seconds: int = DEFAULT_COOLDOWN):
    autonomy_state["cooldowns"][key] = datetime.now() + timedelta(seconds=seconds)


def _make_suggestion(key: str, text: str):
    """Register a suggestion and speak it."""
    autonomy_state["waiting_for_confirmation"] = True
    autonomy_state["last_suggestion"] = text
    autonomy_state["last_suggestion_key"] = key
    autonomy_state["last_suggestion_time"] = datetime.now()
    _set_cooldown(key)
    speak(text)


def autonomous_check(last_interaction_time, emotion: str | None):
    """
    Called periodically from ptt.py main loop.
    Decides if JARVIS should suggest something.
    """
    if autonomy_state["waiting_for_confirmation"]:
        return  # already waiting on user

    now = time.time()
    stress, fatigue = mem.get_health()
    baseline_emotion = mem.get_baseline_emotion()

    idle = (now - last_interaction_time) if last_interaction_time else 0
    now_dt = datetime.now()
    hour = now_dt.hour

    # ---------- TIME-BASED ----------
    # Morning briefing
    if 6 <= hour <= 10 and not _on_cooldown("morning_briefing"):
        if mem.is_routine_time("check_agenda"):
            _make_suggestion("morning_briefing", "Good morning. Do you want me to give you a briefing for today?")
            return

    # Evening wrap-up
    if 20 <= hour <= 23 and not _on_cooldown("evening_wrapup"):
        _make_suggestion("evening_wrapup", "It's getting late. Do you want me to summarize your day and prepare tomorrow?")
        return

    # Night wake suggestion
    if 21 <= hour <= 23 and not _on_cooldown("wake_setup"):
        if fatigue > 0.5:
            _make_suggestion("wake_setup", "You sound a bit tired. Do you want me to set a wake-up time for tomorrow?")
            return

    # ---------- IDLE / HEALTH ----------
    if idle > 600 and not _on_cooldown("long_idle_check"):
        if stress > 0.6 or fatigue > 0.6:
            _make_suggestion("long_idle_check", "You’ve been quiet for a while. Do you want to take a short break?")
            return

    # ---------- EMOTION-BASED ----------
    if emotion in ["angry", "frustrated", "stressed"] and not _on_cooldown("stress_help"):
        _make_suggestion("stress_help", "You sound a bit tense. Do you want to take a short break or reorganize your tasks?")
        return

    if emotion in ["sad", "tired"] and not _on_cooldown("tired_help"):
        _make_suggestion("tired_help", "You sound tired. Do you want me to set a wake-up time or read your agenda for tomorrow?")
        return

    if emotion in ["happy", "excited"] and not _on_cooldown("creative_push"):
        _make_suggestion("creative_push", "You sound energized. Do you want to continue your last project or start something new?")
        return

    # ---------- ROUTINE-BASED ----------
    if mem.is_routine_time("send_text") and not _on_cooldown("send_text"):
        _make_suggestion("send_text", "Around this time you usually send a message. Do you want to send one now?")
        return

    if mem.is_routine_time("check_train") and not _on_cooldown("check_train"):
        _make_suggestion("check_train", "You usually check your train around now. Do you want me to check if it's delayed?")
        return

    if mem.is_routine_time("start_planning") and not _on_cooldown("start_planning"):
        _make_suggestion("start_planning", "You often plan your work around this time. Do you want to plan something?")
        return

    # You can keep adding more here: context, apps, CAD, etc.


def handle_autonomy_response(raw_text: str):
    """
    Called from brain.process_text when user says something
    and autonomy_state['waiting_for_confirmation'] is True.
    Returns:
      - None if handled and nothing more to say
      - A string if JARVIS should say something
    """
    if not autonomy_state["waiting_for_confirmation"]:
        return None

    t = raw_text.lower()

    if any(x in t for x in ["yes", "sure", "okay", "ok", "do it", "go ahead"]):
        key = autonomy_state["last_suggestion_key"]
        suggestion = autonomy_state["last_suggestion"]

        autonomy_state["waiting_for_confirmation"] = False
        autonomy_state["last_suggestion"] = None
        autonomy_state["last_suggestion_key"] = None

        return execute_autonomous_action(key, suggestion)

    if any(x in t for x in ["no", "not now", "stop", "cancel"]):
        autonomy_state["waiting_for_confirmation"] = False
        autonomy_state["last_suggestion"] = None
        autonomy_state["last_suggestion_key"] = None
        return "Alright, I won't."

    # unclear answer
    return "Should I do that?"


def execute_autonomous_action(key: str, suggestion_text: str):
    """
    Map suggestion keys to real actions.
    This is where we hook into brain / other modules.
    """
    from calander_manager import get_briefing, start_planning
    from check_ns import check_train_delay
    from datetime import datetime
    import brain
    import helpers

    # Morning briefing
    if key == "morning_briefing":
        return get_briefing(helpers.reminder_manager)

    # Evening wrap-up
    if key == "evening_wrapup":
        # You can make this richer later (summarize notes, reminders, etc.)
        notes = brain.read_notes() if hasattr(brain, "read_notes") else ""
        return f"Today you worked on: {notes or 'no notes recorded.'}"

    # Wake setup
    if key == "wake_setup":
        # Start wake dialog in brain
        if hasattr(brain, "start_wake_dialog"):
            brain.start_wake_dialog()
            return None
        return "Tell me what time I should wake you."

    # Long idle break
    if key == "long_idle_check":
        helpers.reminder_manager.add_in(10, "Take a short break")
        return "Okay, I'll remind you to take a break in 10 minutes."

    # Stress help
    if key == "stress_help":
        helpers.reminder_manager.add_in(5, "Take a short breathing break")
        return "Okay, I'll remind you in a few minutes to take a short breathing break."

    # Tired help
    if key == "tired_help":
        return "If you want, you can say 'set a wake-up time' or 'read my agenda for tomorrow'."

    # Creative push
    if key == "creative_push":
        return "You can say 'start a new project' or 'open the CAD viewer' if you want to build something."

    # Send text
    if key == "send_text":
        if hasattr(brain, "start_whatsapp_dialog"):
            brain.start_whatsapp_dialog()
            return None
        return "You can tell me who to message and what to say."

    # Check train
    if key == "check_train":
        result = check_train_delay("Cl", "Ehv", datetime.now())
        if not result:
            return "I couldn't find your train."
        if result["delay"] and result["delay"] > 0:
            minutes = result["delay"] // 60
            return f"Your train is delayed by {minutes} minutes."
        else:
            return "Your train seems to be on time."

    # Start planning
    if key == "start_planning":
        start_planning("autonomous")
        return None

    # Fallback
    return "Done."
