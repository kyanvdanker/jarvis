import threading
import subprocess
import sys
import webbrowser
import os
from gui_main import ui
import PTT


# -------------------------
# START BACKEND (Jarvis brain)
# -------------------------
def start_backend():
    PTT.main()


# -------------------------
# START API SERVER (uvicorn)
# -------------------------
def start_api_server():
    subprocess.run([
        sys.executable,
        "-m",
        "uvicorn",
        "server:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


# -------------------------
# START WEB SERVER (static files)
# -------------------------
def start_web_server():
    web_dir = os.path.join(os.getcwd(), "web")
    subprocess.run([
        sys.executable,
        "-m",
        "http.server",
        "8080",
        "--directory",
        web_dir
    ])


# -------------------------
# START PI SERVER (server_pi.py)
# -------------------------
def start_pi_server():
    subprocess.run([
        sys.executable,
        os.path.join("server", "server_pi.py")
    ])


# -------------------------
# MAIN LAUNCHER
# -------------------------
def main():
    # Start backend (PTT) in background
    threading.Thread(target=start_backend, daemon=True).start()

    # Start API server in background
    threading.Thread(target=start_api_server, daemon=True).start()

    # Start web server in background
    threading.Thread(target=start_web_server, daemon=True).start()

    # Start Pi server in background
    threading.Thread(target=start_pi_server, daemon=True).start()

    # Open browser automatically
    webbrowser.open("http://localhost:8080")

    # Run GUI in main thread
    ui.run()


if __name__ == "__main__":
    main()
