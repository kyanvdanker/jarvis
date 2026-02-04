# handlers/audio_handler.py
import os
import time

async def handle_audio(ws, data):
    device = data["device"]
    chunk_hex = data["data"]
    gain = data.get("gain")
    rms = data.get("rms")

    # Convert hex → bytes
    audio_bytes = bytes.fromhex(chunk_hex)

    # Save chunk
    filename = f"storage/audio_chunks/{device}_{int(time.time()*1000)}.raw"
    with open(filename, "wb") as f:
        f.write(audio_bytes)

    # You can forward this to Whisper or your AI pipeline here
