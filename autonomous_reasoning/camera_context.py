import vision.camera_control as cam
from speak import speak
import brain

def camera_based_suggestions():
    # 1. If you're writing/working → offer reasoning mode
    if cam.current_activity in ["writing", "working"]:
        if not brain.reasoning_state["active"]:
            speak("I see you're working. Want me to switch to reasoning mode so we can think through it together?")
            brain.autonomy_state["last_suggestion"] = "switch_to_reasoning"
            brain.autonomy_state["waiting_for_confirmation"] = True
            return

    # 2. Electronics detected
    electronics = {"resistor", "capacitor", "breadboard", "arduino", "pcb", "servo", "motor"}
    if any(obj in cam.current_objects for obj in electronics):
        speak("Looks like you're working with electronics. Are you building a circuit or testing a component?")
        return

    # 3. Materials detected
    materials = {"aluminum", "steel", "carbon", "wood", "plastic", "nylon", "petg", "pla"}
    if any(obj in cam.current_objects for obj in materials):
        speak("I see some materials on your desk. Is this for your current project?")
        return
