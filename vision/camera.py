import cv2

def camera_loop(callback):
    print("Camera loop started")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Camera not available")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        callback(frame)

        # REMOVE the window:
        # cv2.imshow("Vision Sandbox", frame)
        # if cv2.waitKey(1) & 0xFF == 27:
        #     break

    cap.release()
    cv2.destroyAllWindows()
