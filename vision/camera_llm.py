import vision.camera_control as cam
from speak import speak
import brain

def camera_autonomous_check():
    # Don't interrupt if waiting for confirmation
    if brain.autonomy_state["waiting_for_confirmation"]:
        return

    # 1. If writing → offer reasoning mode
    if cam.current_activity == "writing":
        if not brain.reasoning_state["active"]:
            speak("I see you're writing. Want me to switch to reasoning mode?")
            brain.autonomy_state["last_suggestion"] = "switch_to_reasoning"
            brain.autonomy_state["waiting_for_confirmation"] = True
            return

    # 2. Electronics detected
    if "electronics" in cam.current_objects or "pcb" in cam.current_objects:
        speak("Looks like you're working with electronics. Are you building a circuit?")
        return

    # 3. Metal detected
    if "metal" in cam.current_objects:
        speak("I see metal parts. Are these for your current project?")
        return
