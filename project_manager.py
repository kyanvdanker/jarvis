import os
import json
from datetime import datetime
import backend
from autonomous_reasoning.llm_reasoner import proactive_review   # <-- your LLM reviewer

ROOT_DIR = "JarvisProjects"
current_project = None


# ------------------ INTERNAL HELPERS ------------------

def _project_path(name):
    return os.path.join(ROOT_DIR, name)

def _meta_path(name):
    return os.path.join(ROOT_DIR, name, "project.json")

def _notes_path(name):
    return os.path.join(ROOT_DIR, name, "notes.txt")


def _load_meta(name):
    path = _meta_path(name)
    if not os.path.exists(path):
        return {
            "name": name,
            "created": str(datetime.now()),
            "requirements": [],
            "materials": [],
            "decisions": []
        }
    with open(path, "r") as f:
        return json.load(f)


def _save_meta(name, data):
    with open(_meta_path(name), "w") as f:
        json.dump(data, f, indent=4)


# ------------------ PROJECT MANAGEMENT ------------------

def project_exists(name: str) -> bool:
    return os.path.exists(_project_path(name))


def create_project(name: str):
    global current_project
    project_path = _project_path(name)

    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, "cad_files"), exist_ok=True)

    # Create notes file
    notes_path = _notes_path(name)
    if not os.path.exists(notes_path):
        with open(notes_path, "w") as f:
            f.write(f"Project {name} created on {datetime.now()}\n\n")

    # Create metadata file
    meta = _load_meta(name)
    _save_meta(name, meta)

    current_project = name
    backend.set_files(os.listdir(project_path))
    backend.set_projects(list_projects())

    return f"Project '{name}' created and selected."


def switch_project(name: str):
    global current_project
    if not project_exists(name):
        return f"Project '{name}' does not exist."

    current_project = name
    backend.set_files(os.listdir(_project_path(name)))
    backend.set_projects(list_projects())

    return f"Switched to project '{name}'."


def list_projects():
    if not os.path.exists(ROOT_DIR):
        return []
    return [
        d for d in os.listdir(ROOT_DIR)
        if os.path.isdir(os.path.join(ROOT_DIR, d))
    ]


# ------------------ NOTES + LLM REVIEW ------------------

def add_note(note: str):
    if current_project is None:
        return "No project selected."

    notes_path = _notes_path(current_project)

    with open(notes_path, "a") as f:
        f.write(f"[{datetime.now()}] {note}\n")

    # Trigger proactive LLM reasoning
    review = proactive_review(note, project_name=current_project)
    if review:
        return f"Note added.\nJarvis insight: {review}"

    return "Note added."


def read_notes():
    if current_project is None:
        return "No project selected."

    notes_path = _notes_path(current_project)
    if not os.path.exists(notes_path):
        return "No notes yet."

    with open(notes_path, "r") as f:
        return f.read()


# ------------------ REQUIREMENTS ------------------

def add_requirement(text: str):
    if current_project is None:
        return "No project selected."

    meta = _load_meta(current_project)
    meta["requirements"].append({
        "text": text,
        "time": str(datetime.now())
    })
    _save_meta(current_project, meta)

    return "Requirement added."


def list_requirements():
    if current_project is None:
        return "No project selected."

    meta = _load_meta(current_project)
    return meta["requirements"]


# ------------------ MATERIALS ------------------

def add_material(material: str):
    if current_project is None:
        return "No project selected."

    meta = _load_meta(current_project)
    meta["materials"].append({
        "material": material,
        "time": str(datetime.now())
    })
    _save_meta(current_project, meta)

    return f"Material '{material}' added."


def list_materials():
    if current_project is None:
        return "No project selected."

    meta = _load_meta(current_project)
    return meta["materials"]


# ------------------ DESIGN DECISIONS ------------------

def add_decision(description: str, reasoning: str = ""):
    if current_project is None:
        return "No project selected."

    meta = _load_meta(current_project)
    meta["decisions"].append({
        "description": description,
        "reasoning": reasoning,
        "time": str(datetime.now())
    })
    _save_meta(current_project, meta)

    return "Design decision added."


def list_decisions():
    if current_project is None:
        return "No project selected."

    meta = _load_meta(current_project)
    return meta["decisions"]
