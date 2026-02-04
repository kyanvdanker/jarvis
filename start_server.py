import subprocess
import sys
import webbrowser
import threading
import os

def start_server():
    subprocess.run([
        sys.executable,
        "-m",
        "uvicorn",
        "server:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

def start_web():
    # Serve the web directory without changing global working directory
    web_dir = os.path.join(os.getcwd(), "web")
    subprocess.run([
        sys.executable,
        "-m",
        "http.server",
        "8080",
        "--directory",
        web_dir
    ])

if __name__ == "__main__":
    # Start web app
    threading.Thread(target=start_web, daemon=True).start()

    # Open browser automatically
    webbrowser.open("http://localhost:8080")

    # Start API server
    start_server()
