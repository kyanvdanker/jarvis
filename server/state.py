# server/state.py
import logging
from typing import Dict
from fastapi import WebSocket

class DeviceManager:
    def __init__(self):
        self.command_sockets: Dict[str, WebSocket] = {}

    async def register_command_socket(self, device_id: str, ws: WebSocket):
        logging.info(f"[dev] Register command socket for {device_id}")
        self.command_sockets[device_id] = ws

    async def unregister_command_socket(self, device_id: str):
        if device_id in self.command_sockets:
            logging.info(f"[dev] Unregister command socket for {device_id}")
            self.command_sockets.pop(device_id, None)

    async def send_command(self, device_id: str, payload: dict):
        ws = self.command_sockets.get(device_id)
        if not ws:
            logging.warning(f"[dev] No command socket for {device_id}")
            return
        await ws.send_json(payload)
