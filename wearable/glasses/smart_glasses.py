import threading
import time
import numpy as np
import sounddevice as sd
import requests
import serial
import pvporcupine
import subprocess

wake_detected = False

SERVER_URL = "http://192.168.2.142:8000/process"
ACCESS_KEY = "SwRSMQXziSaF9ZcqpSgZDUpUW8HusjVIo8CWwmFsFVsW8vrP8H8mew=="
SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

# -----------------------------
# SERIAL TO ARDUINO
# -----------------------------
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

def send_to_arduino(text: str):
    ser.write((text + "\n").encode("utf-8"))


# -----------------------------
# TEXT PAGINATION FOR DISPLAY
# -----------------------------
def paginate_text(text, max_chars=22):
    words = text.split()
    pages = []
    current = ""

    for w in words:
        if len(current) + len(w) + 1 > max_chars:
            pages.append(current.strip())
            current = ""
        current += w + " "

    if current.strip():
        pages.append(current.strip())

    return pages



# -----------------------------
# TEXT TO SPEECH (TTS)
# -----------------------------
def speak(text):
    # Example using Piper TTS
    # subprocess.run(["piper", "-m", "en_US-amy-medium", "-t", text])
    print("TTS:", text)


# -----------------------------
# SPEECH TO TEXT (STT)
# -----------------------------
def speech_to_text(audio, sample_rate):
    # Placeholder — integrate Whisper, Vosk, etc.
    return "<recognized speech>"


# -----------------------------
# SEND TO SERVER
# -----------------------------
def send_to_server(text):
    try:
        r = requests.post(SERVER_URL, json={"text": text}, timeout=30)
        r.raise_for_status()
        return r.json().get("reply")
    except Exception as e:
        print("Server error:", e)
        return None


# -----------------------------
# RECORDING WITH SILENCE DETECTION
# -----------------------------
def record_utterance(max_duration=5.0, silence_ms=800, energy_thresh=300):
    sample_rate = 16000
    blocksize = 1024
    silence_blocks_needed = int((silence_ms / 1000) * sample_rate / blocksize)

    audio_chunks = []
    silent_blocks = 0
    start_time = time.time()

    with sd.InputStream(
        channels=1,
        samplerate=sample_rate,
        blocksize=blocksize,
        dtype='int16'
    ) as stream:

        while True:
            pcm, _ = stream.read(blocksize)
            data = np.frombuffer(pcm, dtype=np.int16)
            audio_chunks.append(data)

            energy = np.abs(data).mean()

            if energy < energy_thresh:
                silent_blocks += 1
            else:
                silent_blocks = 0

            if silent_blocks >= silence_blocks_needed:
                print("Silence detected → stopping")
                break

            if time.time() - start_time > max_duration:
                print("Max duration reached → stopping")
                break

    audio = np.concatenate(audio_chunks)
    return audio, sample_rate


# -----------------------------
# WAKE WORD LISTENER
# -----------------------------
def porcupine_listener():
    global wake_detected

    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keywords=["jarvis"]
    )

    frame_length = porcupine.frame_length
    sample_rate = porcupine.sample_rate

    with sd.InputStream(
        channels=1,
        samplerate=sample_rate,
        blocksize=frame_length,
        dtype='int16'
    ) as stream:

        while True:
            pcm, _ = stream.read(frame_length)
            pcm = np.frombuffer(pcm, dtype=np.int16)

            if porcupine.process(pcm) >= 0:
                print("\nWake word detected!")
                wake_detected = True


# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    global wake_detected

    threading.Thread(target=porcupine_listener, daemon=True).start()

    print("Jarvis listening...")
    last_heartbeat = time.time()

    while True:
        if not wake_detected:
            if time.time() - last_heartbeat > 5: 
                send_to_arduino("<IDLE>") 
                last_heartbeat = time.time()
            time.sleep(0.05)
            continue

        wake_detected = False
        print("Listening for command...")
        send_to_arduino("<LISTEN>")

        audio, sr = record_utterance()
        text = speech_to_text(audio, sr)

        if not text or text.strip() == "":
            print("No speech recognized.")
            continue

        print("You said:", text)

        reply = send_to_server(text)
        if not reply:
            print("No reply from server.")
            continue

        print("Jarvis:", reply)

        # Speak it
        speak(reply)

        # Paginate for display
        pages = paginate_text(reply)

        for p in pages:
            send_to_arduino(p)
            time.sleep(2.5)  # reading pace


if __name__ == "__main__":
    main()
