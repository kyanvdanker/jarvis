import os
import datetime

project_directories = "Projects"

project_status = {
    "name": None
}

def speak(text):
    print(text)

def switch_project(project_name: str):
    if os.path.isdir(f"{project_directories}/{project_name}"):
        project_status["name"] = project_name
        speak(f"Switching to project {project_name}")
    else:
        speak(f"Project {project_name} does not exist")

def create_project(project_name: str):
    path = f"{project_directories}/{project_name}"
    if not os.path.isdir(path):
        os.makedirs(path)
        speak(f"Created project {project_name}")
    else:
        speak(f"Project {project_name} already exists")

def add_memo(memo: str):
    if project_status["name"] is None:
        speak("No project selected. Please switch to a project first.")
        return
    project_name = project_status["name"]
    timestamp = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
    with open(f"{project_directories}/{project_name}/memos.txt", "a") as f:
        f.write(timestamp + memo + "\n")
    speak("Memo added to project")

def list_projects():
    projects = os.listdir(project_directories)
    if projects:
        speak("Available projects:")
        for proj in projects:
            speak(f"- {proj}")
    else:
        speak("No projects found.")

def read_memos():
    if project_status["name"] is None:
        speak("No project selected. Please switch to a project first.")
        return
    project_name = project_status["name"]
    memo_file = f"{project_directories}/{project_name}/memos.txt"
    if os.path.isfile(memo_file):
        speak(f"Memos for project {project_name}:")
        with open(memo_file, "r") as f:
            memos = f.readlines()
            for memo in memos:
                speak(memo.strip())
    else:
        speak("No memos found for this project.")

def open_file(filename: str):
    if project_status["name"] is None:
        speak("No project selected. Please switch to a project first.")
        return
    project_name = project_status["name"]
    file_path = f"{project_directories}/{project_name}/{filename}"
    if os.path.isfile(file_path):
        os.startfile(file_path)
        speak(f"Opening {filename} in project {project_name}")
    else:
        speak(f"File {filename} does not exist in project {project_name}")