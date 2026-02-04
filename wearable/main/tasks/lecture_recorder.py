# tasks/lecture_recorder.py
import time
import logging
import numpy as np

class LectureRecorderTask:
    def __init__(self, network, audio, sensors, hud, location, settings):
        self.network = network
        self.audio = audio
        self.settings = settings
        self.running = True
        self.enabled = True

        # Auto-gain parameters
        self.target_rms = 3000       # desired loudness
        self.gain = 1.0              # multiplier
        self.max_gain = 4.0
        self.min_gain = 0.25

    def _auto_gain(self, pcm_bytes):
        """Adjust gain based on RMS loudness."""
        samples = np.frombuffer(pcm_bytes, dtype=np.int16)
        rms = np.sqrt(np.mean(samples**2))

        if rms > 0:
            ratio = self.target_rms / rms
            self.gain *= ratio

        # Clamp gain
        self.gain = max(self.min_gain, min(self.gain, self.max_gain))

        # Apply gain
        adjusted = np.clip(samples * self.gain, -32768, 32767).astype(np.int16)
        return adjusted.tobytes(), rms

    def run(self):
        logging.info("LectureRecorderTask started.")

        while self.running:
            if not self.enabled:
                time.sleep(0.5)
                continue

            raw = self.audio.record_chunk(duration=1.0)
            if not raw:
                continue

            # Auto-gain
            adjusted, rms = self._auto_gain(raw)

            # Send audio chunk
            packet = {
                "type": "audio_chunk",
                "device": self.settings.DEVICE_ID,
                "gain": self.gain,
                "rms": float(rms),
                "data": adjusted.hex()
            }
            self.network.send(packet)

            # Lab notebook hook
            self.network.send({
                "type": "labnote_audio_meta",
                "device": self.settings.DEVICE_ID,
                "timestamp": time.time(),
                "gain": self.gain,
                "rms": float(rms)
            })

            time.sleep(0.1)

    def stop(self):
        self.running = False
