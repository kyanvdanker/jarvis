import asyncio
import logging
import json
import websockets
import requests

from config import COMMAND_WS_URL, PUSHCUT_WEBHOOK, NTFY_TOPIC

class CommandClient:
    def __init__(self):
        self._stop = asyncio.Event()
        self._task = None

    async def run(self):
        backoff = 1
        while not self._stop.is_set():
            try:
                logging.info(f"[cmd] Connecting {COMMAND_WS_URL}")
                async with websockets.connect(COMMAND_WS_URL) as ws:
                    logging.info("[cmd] Connected")
                    backoff = 1
                    async for message in ws:
                        try:
                            cmd = json.loads(message)
                            await self._handle_command(cmd)
                        except Exception:
                            logging.exception("[cmd] handle error")
            except Exception as e:
                logging.exception(f"[cmd] fail: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 1.8 + 0.5, 60)

    async def _handle_command(self, cmd: dict):
        kind = cmd.get("type")
        if kind == "tts":
            text = cmd.get("text", "")
            if text:
                try:
                    url = PUSHCUT_WEBHOOK + requests.utils.quote(text)
                    r = requests.get(url, timeout=5)  # Pushcut uses GET for simple input
                    if r.ok:
                        logging.info(f"[TTS] Sent to phone: {text}")
                        return
                except Exception as e:
                    logging.error(f"[TTS] Pushcut fail: {e}")
                # Fallback ntfy
                requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=text.encode(), headers={"Title": "Jarvis"})
        elif kind == "notify":
            text = cmd.get("message", "")
            requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=text.encode(), headers={"Title": "Jarvis Alert"})
        elif kind in ("summarize_session", "safety_alert"):
            # Forward to phone
            text = cmd.get("summary") or cmd.get("reason") or "Alert from Jarvis"
            requests.post(f"https://ntfy.sh/{NTFY_TOPIC}", data=text.encode(), headers={"Priority": "high", "Title": "Jarvis"})
        else:
            logging.warning(f"[cmd] unknown: {kind}")

    def start(self):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run())

    def stop(self):
        self._stop.set()