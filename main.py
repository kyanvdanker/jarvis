from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QUrl
from backend.bridge import Backend
import PTT
import sys
import threading

backend = Backend()   # <‑‑ CREATE INSTANCE HERE

def main():
    app = QGuiApplication(sys.argv)

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)

    engine.load(QUrl("ui/MainWindow.qml"))
    if not engine.rootObjects():
        sys.exit(-1)

    threading.Thread(target=PTT.main, daemon=True).start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
