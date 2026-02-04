import threading
import time
import signal
import logging
from config.settings import Settings

# Services
from services.network import NetworkService
from services.audio import AudioService
from services.sensors import SensorService
from services.location import LocationService

# Tasks
from tasks.lecture_recorder import LectureRecorderTask
from tasks.environment_monitor import EnvironmentMonitorTask
from tasks.heartbeat import HeartbeatTask
from tasks.motion import MotionTask



class WearableMain:
    def __init__(self):
        self.running = True
        self.settings = Settings()

        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        )

        logging.info("Initializing services...")

        # Initialize services
        self.network = NetworkService(self.settings)
        self.audio = AudioService(self.settings)
        self.sensors = SensorService(self.settings)
        self.location = LocationService(self.settings)

        # Task registry
        self.tasks = []

    def start_tasks(self):
        logging.info("Starting tasks...")

        task_classes = [
            LectureRecorderTask,
            EnvironmentMonitorTask,
            HeartbeatTask,
            MotionTask
        ]

        for task_cls in task_classes:
            task = task_cls(
                network=self.network,
                audio=self.audio,
                sensors=self.sensors,
                hud=self.hud,
                location=self.location,
                settings=self.settings
            )
            thread = threading.Thread(target=self._task_wrapper, args=(task,), daemon=True)
            self.tasks.append((task, thread))
            thread.start()
            logging.info(f"Started task: {task_cls.__name__}")

    def _task_wrapper(self, task):
        """Ensures tasks auto-restart if they crash."""
        while self.running:
            try:
                task.run()
            except Exception as e:
                logging.error(f"Task {task.__class__.__name__} crashed: {e}")
                time.sleep(1)
                logging.info(f"Restarting task {task.__class__.__name__}...")

    def stop(self):
        logging.info("Shutting down wearable...")
        self.running = False

        # Stop tasks
        for task, _ in self.tasks:
            if hasattr(task, "stop"):
                task.stop()

        # Stop services
        self.network.stop()
        self.audio.stop()
        self.sensors.stop()
        self.hud.stop()
        self.location.stop()

        logging.info("Shutdown complete.")

    def run(self):
        logging.info("Wearable started.")
        self.start_tasks()

        # Handle Ctrl+C
        signal.signal(signal.SIGINT, lambda sig, frame: self.stop())

        while self.running:
            time.sleep(0.5)


if __name__ == "__main__":
    app = WearableMain()
    app.run()
