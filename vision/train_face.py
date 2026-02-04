import cv2
import os
import numpy as np

TRAIN_IMG = "vision/WIN_20260121_20_49_37_Pro.jpg"
MODEL_PATH = "c:/Jarvis/models/kyan_lbph.xml"

# Haar cascade
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

img = cv2.imread(TRAIN_IMG)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

faces = face_cascade.detectMultiScale(gray, 1.3, 5)
if len(faces) == 0:
    raise RuntimeError("No face found in training image")

(x, y, w, h) = faces[0]
face_roi = gray[y:y+h, x:x+w]

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train([face_roi], np.array([1]))  # label 1 = Kyan
recognizer.save(MODEL_PATH)

print("Training complete. Model saved.")
