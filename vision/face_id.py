import cv2
import time
import numpy as np

# Path to your trained LBPH model
MODEL_PATH = "c:/Jarvis/models/kyan_lbph.xml"

# Haar cascade for face detection
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

# Load recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(MODEL_PATH)

last_seen_time = 0
SEEN_COOLDOWN = 60 * 5  # 5 minutes


def detect_kyan(frame):
    global last_seen_time

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        return False, False

    (x, y, w, h) = faces[0]
    face_roi = gray[y:y+h, x:x+w]

    # Predict identity
    label, confidence = recognizer.predict(face_roi)

    # LBPH: lower confidence = better match
    is_kyan = (label == 1 and confidence < 60)

    if is_kyan:
        now = time.time()
        greet = (now - last_seen_time) > SEEN_COOLDOWN
        last_seen_time = now
        return True, greet

    return False, False
