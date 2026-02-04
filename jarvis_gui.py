import sys
import math
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel


class JarvisCoreWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)

        self.angle_outer = 0
        self.angle_middle = 0
        self.angle_inner = 0

        self.base_radius = 70
        self.pulse_radius = 0
        self.pulse_target = 0
        self.pulse_speed = 4

        self.is_listening = False
        self.is_speaking = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS

    def set_listening(self, listening: bool):
        self.is_listening = listening

    def set_speaking(self, speaking: bool):
        self.is_speaking = speaking
        if speaking:
            self.pulse_target = 40  # expand
        else:
            self.pulse_target = 0   # contract

    def update_animation(self):
        # Rotate rings
        self.angle_outer = (self.angle_outer + 0.4) % 360
        self.angle_middle = (self.angle_middle - 0.7) % 360
        self.angle_inner = (self.angle_inner + 1.1) % 360

        # Pulse radius easing
        if self.pulse_radius < self.pulse_target:
            self.pulse_radius += self.pulse_speed
        elif self.pulse_radius > self.pulse_target:
            self.pulse_radius -= self.pulse_speed

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        center = QPointF(w / 2, h / 2)

        painter.fillRect(self.rect(), QColor(5, 10, 20))

        # Glow background
        gradient_color = QColor(0, 200, 255, 40)
        painter.setBrush(QBrush(gradient_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, 140, 140)

        # Pulse ring (speaking)
        if self.pulse_radius > 0:
            pulse_color = QColor(0, 220, 255, 120)
            pen = QPen(pulse_color, 3)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, self.base_radius + self.pulse_radius,
                                self.base_radius + self.pulse_radius)

        # Outer rotating ring
        self.draw_ring(painter, center, 120, 8, self.angle_outer, QColor(0, 180, 255, 180))

        # Middle rotating ring
        self.draw_ring(painter, center, 95, 6, self.angle_middle, QColor(0, 220, 255, 200))

        # Inner rotating ring
        self.draw_ring(painter, center, 70, 4, self.angle_inner, QColor(0, 255, 255, 220))

        # Core
        core_color = QColor(0, 255, 255, 230 if self.is_listening or self.is_speaking else 160)
        painter.setBrush(QBrush(core_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, self.base_radius, self.base_radius)

        # Core inner glow
        inner_color = QColor(255, 255, 255, 200)
        painter.setBrush(QBrush(inner_color))
        painter.drawEllipse(center, self.base_radius * 0.4, self.base_radius * 0.4)

    def draw_ring(self, painter, center, radius, thickness, angle, color):
        pen = QPen(color, thickness)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Draw partial arcs to look more "tech"
        span_deg = 60
        for offset in (0, 120, 240):
            start_angle = int((angle + offset) * 16)
            span_angle = int(span_deg * 16)
            rect = self._circle_rect(center, radius)
            painter.drawArc(rect, start_angle, span_angle)

    def _circle_rect(self, center, radius):
        return (
            int(center.x() - radius),
            int(center.y() - radius),
            int(radius * 2),
            int(radius * 2),
        )


class JarvisWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jarvis Interface")
        self.setStyleSheet("background-color: #050A14; color: #00FFFF;")

        self.core = JarvisCoreWidget(self)

        self.text_label = QLabel("Awaiting command...", self)
        self.text_label.setStyleSheet("font-size: 16px; color: #00FFFF;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gesture_label = QLabel("Gesture: None", self)
        self.gesture_label.setStyleSheet("font-size: 14px; color: #00AACC;")
        self.gesture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.core, stretch=4)
        layout.addWidget(self.text_label, stretch=1)
        layout.addWidget(self.gesture_label, stretch=1)
        self.setLayout(layout)

        self.resize(600, 700)

    # Public API for your PTT loop
    def set_listening(self, listening: bool):
        self.core.set_listening(listening)

    def set_speaking(self, speaking: bool):
        self.core.set_speaking(speaking)

    def update_text(self, text: str):
        self.text_label.setText(text)

    def update_gesture(self, gesture: str):
        self.gesture_label.setText(f"Gesture: {gesture}")


# Singleton app/window for external control
_app = None
_window = None

def start_gui():
    global _app, _window
    if _app is not None:
        return

    _app = QApplication(sys.argv)
    _window = JarvisWindow()
    _window.show()

    # Run in a non-blocking way if you want to integrate with other loops
    QTimer.singleShot(0, lambda: None)
    _app.exec()


def get_window():
    return _window
