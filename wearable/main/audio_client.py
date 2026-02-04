import asyncio
import threading
import logging
import time
import websockets
import sounddevice as sd
import numpy as np
import webrtcvad

from config import AUDIO_WS_URL, SAMPLE_RATE, BLOCK_SIZE

class AudioClient:
    def __init__(self):
        self.vad = webrtcvad.Vad(mode=1)  # 0=off, 1=low, 2=mid, 3=aggressive
        self._stop = asyncio.Event()
        self._muted = False
        self.last_speech_detected = False
        self._last_ok = time.time()
        self._task = None

    def set_muted(self, muted: bool):
        self._muted = muted
        logging.info(f"Audio muted: {muted}")

    async def run(self):
        backoff = 1
        while not self._stop.is_set():
            if self._muted:
                await asyncio.sleep(1)
                continue
            try:
                logging.info(f"[audio] Connecting {AUDIO_WS_URL}")
                async with websockets.connect(AUDIO_WS_URL, max_size=None) as ws:
                    logging.info("[audio] Connected")
                    backoff = 1

                    loop = asyncio.get_running_loop()

                    def callback(indata, frames, time_info, status):
                        if status:
                            logging.warning(f"[audio] {status}")
                        if self._stop.is_set() or self._muted:
                            raise sd.CallbackAbort
                        audio_bytes = indata.tobytes()
                        is_speech = self.vad.is_speech(audio_bytes, SAMPLE_RATE)
                        self.last_speech_detected = is_speech
                        if is_speech:
                            try:
                                asyncio.run_coroutine_threadsafe(ws.send(audio_bytes), loop)
                            except Exception:
                                logging.exception("[audio] send fail")
                        self._last_ok = time.time()

                    with sd.InputStream(
                        samplerate=SAMPLE_RATE,
                        channels=1,
                        dtype="int16",
                        blocksize=BLOCK_SIZE,
                        callback=callback,
                    ):
                        while not self._stop.is_set() and not self._muted:
                            await asyncio.sleep(0.2)

            except Exception as e:
                logging.exception(f"[audio] error: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.8 + 0.5, 30)

    def start(self):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run())

    def tick(self):
        if time.time() - self._last_ok > 20:
            logging.warning("[audio] stalled → reconnect")
            self.stop()
            self.start()

    def stop(self):
        self._stop.set()