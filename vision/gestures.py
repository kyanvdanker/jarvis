import cv2
import numpy as np
import mediapipe as mp
import time
from collections import deque
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "c:/Jarvis/models/hand_landmarker.task"

base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    running_mode=vision.RunningMode.VIDEO
)

landmarker = vision.HandLandmarker.create_from_options(options)

# History buffers for smoothing
center_history = deque(maxlen=5)
angle_history = deque(maxlen=5)
size_history = deque(maxlen=5)

prev_center = None
prev_angle = None
prev_size = None

last_gesture_time = 0
COOLDOWN = 0.30  # seconds

# Thresholds tuned for stability + responsiveness
SWIPE_THRESHOLD = 0.08
VERTICAL_ROT_THRESHOLD = 0.04
ROTATION_THRESHOLD = 15
ZOOM_THRESHOLD = 0.02
DEADZONE = 0.01


def get_hand_center(hand):
    xs = [p.x for p in hand]
    ys = [p.y for p in hand]
    return np.mean(xs), np.mean(ys)


def get_hand_size(hand):
    return np.hypot(hand[0].x - hand[12].x, hand[0].y - hand[12].y)


def get_index_angle(hand):
    dx = hand[8].x - hand[5].x
    dy = hand[8].y - hand[5].y
    return np.degrees(np.arctan2(dy, dx))


def detect_gesture(frame, timestamp_ms):
    global prev_center, prev_angle, prev_size, last_gesture_time

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect_for_video(mp_image, timestamp_ms)

    if not result.hand_landmarks:
        prev_center = prev_angle = prev_size = None
        return None

    hand = result.hand_landmarks[0]

    # Detect open hand
    thumb = hand[4]
    index = hand[8]
    pinch_dist = np.hypot(thumb.x - index.x, thumb.y - index.y)
    is_open_hand = pinch_dist > 0.06
    is_pinch = pinch_dist < 0.03

    # Motion features
    center = get_hand_center(hand)
    angle = get_index_angle(hand)
    size = get_hand_size(hand)

    # Add to smoothing buffers
    center_history.append(center)
    angle_history.append(angle)
    size_history.append(size)

    # Smoothed values
    center_s = np.mean(center_history, axis=0)
    angle_s = np.mean(angle_history)
    size_s = np.mean(size_history)

    gesture = None
    hand_move = False
    d_angle = 0

    if prev_center is not None:
        dx = center_s[0] - prev_center[0]
        dy = center_s[1] - prev_center[1]
        d_angle = angle_s - prev_angle
        d_size = size_s - prev_size

        # Deadzone filtering
        if abs(dx) < DEADZONE: dx = 0
        if abs(dy) < DEADZONE: dy = 0
        if abs(d_angle) < 5: d_angle = 0

        # Detect continuous hand movement (for object dragging)
        if abs(dx) > DEADZONE or abs(dy) > DEADZONE:
            hand_move = True

        # Cooldown
        if time.time() - last_gesture_time > COOLDOWN:

            # Pinch gesture (grab)
            if is_pinch:
                gesture = "pinch"

            # Open hand (release)
            elif is_open_hand and not is_pinch:
                gesture = "open_hand"

            # ROTATION LEFT/RIGHT (index finger angle)
            if abs(d_angle) > ROTATION_THRESHOLD:
                gesture = "rotate_right" if d_angle > 0 else "rotate_left"

            # ROTATION UP/DOWN (hand vertical movement)
            if abs(dy) > VERTICAL_ROT_THRESHOLD:
                gesture = "rotate_up" if dy < 0 else "rotate_down"

            # ZOOM OUT (open hand moving away)
            if is_open_hand and d_size < -ZOOM_THRESHOLD:
                gesture = "zoom_out"

            # ZOOM IN (open hand moving toward camera)
            if is_open_hand and d_size > ZOOM_THRESHOLD:
                gesture = "zoom_in"

            # SWIPES (open hand)
            if is_open_hand:
                if dx < -SWIPE_THRESHOLD:
                    gesture = "swipe_left"
                elif dx > SWIPE_THRESHOLD:
                    gesture = "swipe_right"
                elif dy < -SWIPE_THRESHOLD:
                    gesture = "swipe_up"
                elif dy > SWIPE_THRESHOLD:
                    gesture = "swipe_down"

            if gesture:
                last_gesture_time = time.time()

    # Update previous smoothed values
    prev_center = center_s
    prev_angle = angle_s
    prev_size = size_s

    if not gesture:
        return None

    # Return full gesture event
    return {
        "intent": gesture,
        "center": center_s,
        "d_angle": d_angle,
        "hand_move": hand_move
    }
