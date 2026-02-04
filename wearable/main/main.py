import asyncio
import logging
import signal
import time
import RPi.GPIO as GPIO

from audio_client import AudioClient
from command_client import CommandClient
from heartbeat import Heartbeat
from context_client import ContextClient
from memory_manager import MemoryManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

async def main_async():
    audio    = AudioClient()
    commands = CommandClient()
    heartbeat = Heartbeat(interval=60)
    context  = ContextClient()
    memory   = MemoryManager(silence_timeout=45)

    logging.info("Jarvis Wearable starting – passive memory + location nudges active")

    audio.start()
    commands.start()
    context.start()

    # Mute button
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MUTE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    muted = False

    def check_mute():
        nonlocal muted
        if GPIO.input(MUTE_PIN) == GPIO.LOW:
            muted = not muted
            audio.set_muted(muted)
            logging.info(f"Streaming {'muted' if muted else 'enabled'}")
            time.sleep(0.3)  # simple debounce

    try:
        while True:
            check_mute()
            audio.tick()
            commands.tick()
            heartbeat.tick()
            context.tick()
            memory.tick(audio.last_speech_detected)
            await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        logging.info("Main loop cancelled")
    finally:
        logging.info("Shutting down components...")
        audio.stop()
        commands.stop()
        context.stop()
        await asyncio.sleep(0.5)
        GPIO.cleanup()

def handle_shutdown(loop):
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)]
    for task in tasks:
        task.cancel()
    loop.stop()

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown, loop)

    try:
        loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received")
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logging.info("Event loop closed")

if __name__ == "__main__":
    main()