# services/audio.py
import sounddevice as sd
import numpy as np
import logging

class AudioService:
    def __init__(self, settings):
        self.settings = settings
        self.running = True

    def record_chunk(self, duration=1.0):
        try:
            audio = sd.rec(
                int(duration * self.settings.AUDIO_RATE),
                samplerate=self.settings.AUDIO_RATE,
                channels=1,
                dtype='int16'
            )
            sd.wait()
            return audio.tobytes()
        except Exception as e:
            logging.error(f"Audio error: {e}")
            return None

    def stop(self):
        self.running = False
