import win32com.client
import pythoncom
import threading
import time
import helpers 

_speak_lock = threading.Lock()
listening_enabled = True

voice = win32com.client.Dispatch("SAPI.SpVoice")
interrupt_flag = threading.Event()

def speak(text: str, interruptible=True, async_mode=True):
    print(helpers.OUTPUT_MODE, "test")
    pythoncom.CoInitialize()

    # --- REMOTE MODE: send text back to server ---
    if helpers.OUTPUT_MODE == "remote":
        print("[REMOTE SPEAK]", text)
        helpers.set_remote_output(text)
        return

    # --- LOCAL MODE: speak out loud ---
    if helpers.OUTPUT_MODE == "local":
        with _speak_lock:
            global listening_enabled
            listening_enabled = False
            print(text)

            if interrupt_flag.is_set():
                return

            flags = 0
            if async_mode:
                flags |= 1

            voice.Speak(text, flags)

            if interruptible:
                def monitor():
                    pythoncom.CoInitialize()
                    start = time.time()
                    while time.time() - start < 45:
                        if interrupt_flag.is_set():
                            voice.Speak("", 1)
                            voice.Skip("Sentence", -1)
                            break
                        time.sleep(0.12)

                threading.Thread(target=monitor, daemon=True).start()

            listening_enabled = True
