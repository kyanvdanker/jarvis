from .camera import camera_loop
from .intents import detect_intent
from .face_id import detect_kyan
import time
import cv2

gesture_mode = "camera"      # "camera" or "object"
object_grabbed = False
last_hand_pos = None

current_activity = "idle"      # "idle", "writing", "working"
current_objects = []           # ["resistor", "aluminum", "pcb"]

camera_verified_user = False
last_seen_kyan = time.time()
viewer_open = False

last_interaction_time = time.time()

def on_frame(frame):
    global object_grabbed, last_hand_pos, gesture_mode
    global last_seen_kyan, camera_verified_user, viewer_open, last_interaction_time
    global current_activity, current_objects

    # Lazy import to avoid circular import
    from gui_viewer import (
        zoom_camera,
        rotate_camera,
        move_object,
        rotate_object
    )

    # ---------------------------------------------------------
    # FACE DETECTION (identity check)
    # ---------------------------------------------------------
    is_kyan, greet = detect_kyan(frame)

    if is_kyan:
        last_seen_kyan = time.time()
        last_interaction_time = time.time()

        if greet:
            from speak import speak
            speak("Welcome back, Kyan.")

        camera_verified_user = True
    else:
        camera_verified_user = False

    # ---------------------------------------------------------
    # ACTIVITY DETECTION (simple placeholder)
    # ---------------------------------------------------------
    # Detect writing posture (hand low + head down)
    if detect_writing_posture(frame):
        current_activity = "writing"
    elif detect_working_posture(frame):
        current_activity = "working"
    else:
        current_activity = "idle"

    # ---------------------------------------------------------
    # OBJECT DETECTION (placeholder)
    # ---------------------------------------------------------
    #labels = detect_objects(frame)  # returns list of strings
    #current_objects = labels


    # ---------------------------------------------------------
    # GESTURES ONLY IF VIEWER IS OPEN
    # ---------------------------------------------------------
    if not viewer_open:
        return

    # ---------------------------------------------------------
    # GESTURE DETECTION
    # ---------------------------------------------------------
    event = detect_intent(frame)
    if not event:
        return
    
    last_interaction_time = time.time()

    intent = event["intent"]
    center = event.get("center")
    d_angle = event.get("d_angle", 0)

    print("Gesture detected:", intent, "mode:", gesture_mode)

    # ---------------------------------------------------------
    # CAMERA MODE
    # ---------------------------------------------------------
    if gesture_mode == "camera":

        if intent == "zoom_in":
            zoom_camera(0.9)
            return

        if intent == "zoom_out":
            zoom_camera(1.1)
            return

        if intent == "rotate_left":
            rotate_camera(dx=-10)
            return

        if intent == "rotate_right":
            rotate_camera(dx=10)
            return

        if intent == "rotate_up":
            rotate_camera(dy=10)
            return

        if intent == "rotate_down":
            rotate_camera(dy=-10)
            return

    # ---------------------------------------------------------
    # OBJECT MODE
    # ---------------------------------------------------------
    if gesture_mode == "object":

        if intent == "pinch" and not object_grabbed:
            object_grabbed = True
            last_hand_pos = center
            print("Object grabbed")
            return

        if object_grabbed and intent == "hand_move":
            dx = center[0] - last_hand_pos[0]
            dy = center[1] - last_hand_pos[1]
            move_object(dx, dy)
            last_hand_pos = center
            return

        if object_grabbed and intent in ("rotate_left", "rotate_right"):
            rotate_object(0, 0, d_angle)
            return

        if object_grabbed and intent == "open_hand":
            object_grabbed = False
            print("Object released")
            return


def start_gesture_camera():
    print("Starting gesture camera...")
    camera_loop(on_frame)
import numpy as np

def detect_writing_posture(frame):
    # Detect head-down posture using brightness + region
    h, w, _ = frame.shape
    lower_region = frame[int(h*0.6):h, :]
    brightness = np.mean(lower_region)

    # If lower region is dark → head is blocking light → writing posture
    return brightness < 60


def detect_working_posture(frame):
    # Detect lots of hand movement in center area
    # Placeholder: always false until you add motion tracking
    return False


def detect_objects(frame):
    # Very lightweight color-based detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    detected = []

    # Detect red (common for wires, components)
    lower_red = np.array([0, 80, 80])
    upper_red = np.array([10, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red, upper_red)
    if np.sum(mask_red) > 5000:
        detected.append("electronics")

    # Detect shiny metal (aluminum)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if np.mean(gray) > 180:
        detected.append("metal")

    # Detect blue (common for PCBs)
    lower_blue = np.array([90, 80, 80])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    if np.sum(mask_blue) > 5000:
        detected.append("pcb")

    return detected

