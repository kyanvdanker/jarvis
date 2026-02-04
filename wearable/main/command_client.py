# wearable/command_client.py
import asyncio
import threading
import logging
import json
import websockets

from config import COMMAND_WS_URL

class CommandClient:
    def __init__(self):
        self._ws_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._ws_thread.start()

    def _run_loop(self):
        asyncio.run(self._loop())

    async def _loop(self):
        while True:
            try:
                logging.info(f"Connecting command WebSocket to {COMMAND_WS_URL}")
                async with websockets.connect(COMMAND_WS_URL) as ws:
                    logging.info("Command WebSocket connected")
                    async for message in ws:
                        try:
                            cmd = json.loads(message)
                            await self._handle_command(cmd)
                        except Exception:
                            logging.exception("Error handling command")
            except Exception:
                logging.exception("Command WebSocket error, retrying in 3s")
                await asyncio.sleep(3)

    async def _handle_command(self, cmd: dict):
        kind = cmd.get("type")
        logging.info(f"Received command: {cmd}")

        if kind == "tts":
            # later: play audio from URL or bytes
            pass
        elif kind == "notify":
            # later: show on display / LED / phone
            pass
        else:
            logging.warning(f"Unknown command type: {kind}")

    def tick(self):
        pass
