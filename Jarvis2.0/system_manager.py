import os
import subprocess

def list_files(path):
    return "\n".join(os.listdir(path))

def open_app(path):
    subprocess.Popen([path])
    return f"Opened application: {path}"
