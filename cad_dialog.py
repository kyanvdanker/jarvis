import os
from cad_library import (
    motor_casing_helper,
    nozzle_helper,
    fin_canister_helper,
    bulkhead_helper,
    engine_mount_helper,
    body_tube_helper,
    nose_cone_helper
)
from viewer import show_object
from helpers import extract_number, generate_filename  # make these helper functions in separate file if not already
from project_manager import current_project
from speak import speak
import vision.camera_control

# --- Component definitions --- #
CAD_COMPONENTS = {
    "motor_casing": {
        "params": [
            ("inner_d", "What is the inner diameter?"),
            ("outer_d", "What is the outer diameter?"),
            ("length", "What is the length?")
        ]
    },
    "nozzle": {
        "params": [
            ("throat_radius", "What is the throat radius?"),
            ("expansion_ratio", "What is the expansion ratio?"),
            ("casing_inner_diameter", "What is the casing inner diameter?")
        ]
    },
    "fin_canister": {
        "params": [
            ("diameter", "What is the diameter?"),
            ("height", "What is the height?"),
            ("fin_slots", "How many fin slots?")
        ]
    },
    "bulkhead": {
        "params": [
            ("diameter", "What is the diameter?"),
            ("thickness", "What is the thickness?")
        ]
    },
    "engine_mount": {
        "params": [
            ("outer_diameter", "What is the outer diameter?"),
            ("inner_diameter", "What is the inner diameter?"),
            ("thickness", "What is the thickness?")
        ]
    },
    "body_tube": {
        "params": [
            ("outer_diameter", "What is the outer diameter?"),
            ("length", "What is the length?"),
            ("wall_thickness", "What is the wall thickness?")
        ]
    },
    "nose_cone": {
        "params": [
            ("base_diameter", "What is the base diameter?"),
            ("height", "What is the height?"),
            ("thickness", "What is the thickness?")
        ]
    }
}

# --- CAD State --- #
cad_state = {
    "active": False,
    "stage": None,          # "collecting" or "confirm"
    "component": None,
    "params": {},
    "dry_run": False
}

last_created = {
    "component": None,
    "params": {}
}


def load_into_viewer(path):
    from gui_viewer import load_stl_into_viewer
    vision.camera_control.viewer_open = True
    load_stl_into_viewer(path)

# --- CAD Dialog --- #
def start_cad_creation(component_name, dry_run=False):
    if current_project is None:
        speak("Please create or switch to a project first.")
        return

    if component_name not in CAD_COMPONENTS:
        speak(f"I don't know how to create {component_name}.")
        return

    cad_state.update({
        "active": True,
        "stage": "collecting",
        "component": component_name,
        "params": {},
        "dry_run": dry_run
    })

    first_prompt = CAD_COMPONENTS[component_name]["params"][0][1]
    speak(first_prompt)


def continue_cad_dialog(text):
    if not cad_state["active"]:
        return

    # cancel anytime
    if any(w in text.lower() for w in ["cancel", "stop", "nevermind"]):
        speak("Cancelled.")
        reset_cad_state()
        return

    component = cad_state["component"]
    spec = CAD_COMPONENTS.get(component)
    params = cad_state["params"]

    # confirmation stage
    if cad_state["stage"] == "confirm":
        if "confirm" in text.lower():
            create_cad_object()
            return
        speak("Say confirm or cancel.")
        return

    # collect next missing parameter
    for name, prompt in spec["params"]:
        if name not in params:
            value = extract_number(text)
            if value is None:
                speak(prompt)
                return
            params[name] = value
            break

    # move to confirm if done
    if all(name in params for name, _ in spec["params"]):
        cad_state["stage"] = "confirm"
        summary = ", ".join(f"{k}={v}" for k, v in params.items())
        speak(f"Creating {component} with {summary}. Say confirm.")


# --- CAD Object Creation --- #
def create_cad_object():
    try:
        c = cad_state["component"]
        p = cad_state["params"]

        # call the correct helper
        helper_map = {
            "motor_casing": motor_casing_helper,
            "nozzle": nozzle_helper,
            "fin_canister": fin_canister_helper,
            "bulkhead": bulkhead_helper,
            "engine_mount": engine_mount_helper,
            "body_tube": body_tube_helper,
            "nose_cone": nose_cone_helper
        }

        if c not in helper_map:
            raise ValueError("Unknown component")

        obj = helper_map[c](**p)

        os.makedirs("output", exist_ok=True)
        filename = generate_filename(c)
        path = f"output/{filename}"
        obj.val().exportStl(path)

        show_object(obj)
        load_into_viewer(path)
        speak("Part created.")

    except Exception as e:
        speak("Error creating part.")
        print("CAD ERROR:", e)
    
        # Save last created part for modification
    last_created["component"] = c
    last_created["params"] = p.copy()
    reset_cad_state()


def reset_cad_state():
    cad_state.update({
        "active": False,
        "stage": None,
        "component": None,
        "params": {},
        "dry_run": False
    })

def modify_last_part(text):
    if not last_created["component"]:
        speak("There is no previous part to modify.")
        return

    comp = last_created["component"]
    params = last_created["params"].copy()

    # Detect which parameter to modify
    for name in params:
        if name.replace("_", " ") in text.lower():
            delta = extract_number(text)
            if delta is None:
                speak("I didn't catch the new value.")
                return

            # Apply modification
            if "increase" in text.lower() or "bigger" in text.lower():
                params[name] += delta
            elif "decrease" in text.lower() or "smaller" in text.lower():
                params[name] -= delta
            else:
                params[name] = delta

            speak(f"Updating {name} to {params[name]}.")
            break
    else:
        speak("I couldn't tell which parameter to modify.")
        return

    # Regenerate part
    helper_map = {
        "motor_casing": motor_casing_helper,
        "nozzle": nozzle_helper,
        "fin_canister": fin_canister_helper,
        "bulkhead": bulkhead_helper,
        "engine_mount": engine_mount_helper,
        "body_tube": body_tube_helper,
        "nose_cone": nose_cone_helper
    }

    obj = helper_map[comp](**params)

    os.makedirs("output", exist_ok=True)
    filename = generate_filename(comp)
    path = f"output/{filename}"
    obj.val().exportStl(path)

    show_object(obj)
    load_into_viewer(path)

    # Save new parameters
    last_created["params"] = params

    speak("Modified part created.")
