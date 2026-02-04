# wearable/main.py
import time
import logging
from audio_client import AudioClient
from command_client import CommandClient
from heartbeat import Heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def main():
    audio = AudioClient()
    commands = CommandClient()
    heartbeat = Heartbeat()

    logging.info("Wearable core starting up")

    while True:
        try:
            audio.tick()
            commands.tick()
            heartbeat.tick()

            # simple place to add periodic health logs later
            time.sleep(0.01)
        except KeyboardInterrupt:
            logging.info("Shutting down wearable core")
            break
        except Exception:
            logging.exception("Error in main loop, backing off")
            time.sleep(2)

if __name__ == "__main__":
    main()
