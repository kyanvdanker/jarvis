from .gestures import detect_gesture
import time

def detect_intent(frame):
    timestamp_ms = int(time.time() * 1000)

    event = detect_gesture(frame, timestamp_ms)

    # event is either:
    #   None
    #   or:
    #   {
    #       "intent": "rotate_left",
    #       "center": (x, y),
    #       "d_angle": -12.3,
    #       "hand_move": True/False
    #   }

    return event
