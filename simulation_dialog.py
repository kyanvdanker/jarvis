from speak import speak
from rocket_simulation import simulate_motor
from helpers import extract_number
import project_manager
import os
import csv

CAD_COMPONENTS_KEYWORDS = {
    "motor_casing": ["motor", "motor casing", "casing"],
    "nozzle": ["nozzle"],
    "fin_canister": ["fin canister", "fin tube", "fin holder"],
    "bulkhead": ["bulkhead", "disc", "plate"],
    "engine_mount": ["engine mount", "mount"],
    "body_tube": ["body tube", "tube", "rocket tube"],
    "nose_cone": ["nose cone", "cone", "nose"]
}


simulation_state = {
    "active": False,
    "stage": None,
    "params": {},
    "results": None,
    "awaiting_save": False
}

SIM_PARAMS = [
    ("R_out", "What is the outer radius in millimeters?"),
    ("R_core", "What is the core radius in millimeters?"),
    ("L_core", "What is the core length in millimeters?"),
    ("P_target", "What is the target pressure in pascals?"),
    ("fins", "How many fins does the motor have?")
]

def start_simulation_dialog():
    simulation_state["active"] = True
    simulation_state["stage"] = 0
    simulation_state["params"] = {}
    simulation_state["results"] = None
    simulation_state["awaiting_save"] = False

    speak("Starting motor simulation. " + SIM_PARAMS[0][1])

def detect_cad_component(text: str):
    t = text.lower()
    for comp, keywords in CAD_COMPONENTS_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return comp
    return None


def continue_simulation_dialog(text):
    # If waiting for save confirmation
    if simulation_state["awaiting_save"]:
        handle_save_confirmation(text)
        return

    if not simulation_state["active"]:
        return

    # Cancel
    if any(w in text.lower() for w in ["cancel", "stop", "nevermind"]):
        speak("Simulation cancelled.")
        simulation_state["active"] = False
        return

    stage = simulation_state["stage"]
    param_name, prompt = SIM_PARAMS[stage]

    if param_name == "P_target":
        value = parse_pressure(text)
    else:
        value = extract_number(text)

    if value is None:
        speak(prompt)
        return

    # Convert mm → meters for radii and length
    if param_name in ["R_out", "R_core", "L_core"]:
        value = value / 1000.0

    simulation_state["params"][param_name] = value
    simulation_state["stage"] += 1

    # If more parameters needed
    if simulation_state["stage"] < len(SIM_PARAMS):
        next_prompt = SIM_PARAMS[simulation_state["stage"]][1]
        speak(next_prompt)
        return

    # All parameters collected → run simulation
    run_simulation()


def run_simulation():
    p = simulation_state["params"]

    result = simulate_motor(
        R_out=p["R_out"],
        R_core=p["R_core"],
        L_core=p["L_core"],
        Density=1700,
        P_target=p["P_target"],
        P_exit=101350,
        n=0.222,
        a=0.00513,
        fins=int(p["fins"]),
        W_fins=0.002,
        L_fins=0.05,
        D_fins=0.016,
        Cd_nozzle=0.65,
        gamma=1.22,
        T=1550,
        R=8.31/0.028,
        Cf=1.4
    )

    simulation_state["results"] = result

    speak(
        f"Simulation complete. Burn time {result['burn_time']:.2f} seconds. "
        f"Average thrust {result['average_thrust']:.1f} newtons. "
        f"Peak thrust {result['peak_thrust']:.1f} newtons. "
        f"Total impulse {result['total_impulse']:.1f} newton seconds. "
        f"Throat diameter {result['throat_diameter']*1000:.2f} millimeters. "
        f"Exit diameter {result['exit_diameter']*1000:.2f} millimeters."
    )

    # Ask to save
    simulation_state["awaiting_save"] = True
    speak("Would you like to save this simulation to your project?")


def handle_save_confirmation(text):
    t = text.lower()

    if any(x in t for x in ["yes", "yeah", "save", "sure", "yep"]):
        save_simulation()
        simulation_state["awaiting_save"] = False
        simulation_state["active"] = False
        speak("Simulation saved to your project.")
        return

    if any(x in t for x in ["no", "don't", "nope", "cancel"]):
        speak("Okay, not saving the simulation.")
        simulation_state["awaiting_save"] = False
        simulation_state["active"] = False
        return

    speak("Please say yes or no.")


def save_simulation():
    if project_manager.current_project is None:
        speak("No project selected. Cannot save simulation.")
        return

    project_path = os.path.join(project_manager.ROOT_DIR, project_manager.current_project)
    os.makedirs(project_path, exist_ok=True)

    file_path = os.path.join(project_path, "simulation_results.csv")

    # Create file if missing
    new_file = not os.path.exists(file_path)

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)

        if new_file:
            writer.writerow([
                "R_out", "R_core", "L_core", "P_target", "fins",
                "burn_time", "mass", "mass_flow", "expansion_ratio",
                "exit_velocity", "throat_diameter", "exit_diameter",
                "expansion_length", "total_impulse", "peak_thrust", "average_thrust"
            ])

        p = simulation_state["params"]
        r = simulation_state["results"]

        writer.writerow([
            p["R_out"], p["R_core"], p["L_core"], p["P_target"], p["fins"],
            r["burn_time"], r["mass"], r["mass_flow"], r["expansion_ratio"],
            r["exit_velocity"], r["throat_diameter"], r["exit_diameter"],
            r["expansion_length"], r["total_impulse"], r["peak_thrust"], r["average_thrust"]
        ])


def parse_pressure(text):
    text = text.lower()

    num = extract_number(text)
    if num is None:
        return None

    if "mpa" in text or "mega" in text:
        return num * 1_000_000
    if "bar" in text:
        return num * 100_000
    if "kpa" in text:
        return num * 1000

    # If user says "2 million"
    if "million" in text:
        return num * 1_000_000

    # If user just says "2" assume MPa (common for motors)
    if num < 5000:  # heuristic
        return num * 1_000_000

    # Otherwise assume Pa
    return num
