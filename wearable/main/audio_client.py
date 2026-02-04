# wearable/audio_client.py
import asyncio
import threading
import logging
import time
import websockets
import sounddevice as sd

from config import AUDIO_WS_URL

class AudioClient:
    def __init__(self, samplerate=16000, blocksize=1024):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self._stop = False
        self._last_ok = 0

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        asyncio.run(self._loop())

    async def _loop(self):
        while not self._stop:
            try:
                logging.info(f"[audio] Connecting to {AUDIO_WS_URL}")
                async with websockets.connect(AUDIO_WS_URL, max_size=None) as ws:
                    logging.info("[audio] Connected")

                    loop = asyncio.get_event_loop()

                    def callback(indata, frames, time_info, status):
                        if status:
                            logging.warning(f"[audio] Status: {status}")
                        try:
                            fut = asyncio.run_coroutine_threadsafe(
                                ws.send(indata.tobytes()), loop
                            )
                        except Exception:
                            logging.exception("[audio] Failed to queue audio chunk")

                    with sd.InputStream(
                        samplerate=self.samplerate,
                        channels=1,
                        dtype="int16",
                        blocksize=self.blocksize,
                        callback=callback,
                    ):
                        while not self._stop:
                            self._last_ok = time.time()
                            await asyncio.sleep(0.1)

            except Exception:
                logging.exception("[audio] WebSocket error, retrying in 3s")
                await asyncio.sleep(3)

    def tick(self):
        # later: expose health (e.g. time since _last_ok)
        pass

    def stop(self):
        self._stop = True
