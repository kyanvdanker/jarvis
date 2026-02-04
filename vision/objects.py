import cv2
from ultralytics import YOLO

# Load YOLO model
model = YOLO("yolov8n.pt")

# Calibration variables
pixel_per_mm = None
reference_width_mm = 25  # width of your reference object in mm (coin, card, etc.)
ref_points = []

# --- Step 1: Manual calibration ---
def click_event(event, x, y, flags, param):
    global ref_points
    if event == cv2.EVENT_LBUTTONDOWN:
        ref_points.append((x, y))
        print(f"Point selected: {x}, {y}")
        if len(ref_points) == 2:
            cv2.destroyAllWindows()

def calibrate_camera():
    global pixel_per_mm, ref_points
    cap = cv2.VideoCapture(0)
    print("Click the left and right edges of your reference object.")
    
    while len(ref_points) < 2:
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.imshow("Calibration", frame)
        cv2.setMouseCallback("Calibration", click_event)
        cv2.waitKey(1)
    
    cap.release()
    cv2.destroyAllWindows()
    
    reference_width_px = abs(ref_points[1][0] - ref_points[0][0])
    pixel_per_mm = reference_width_px / reference_width_mm
    print(f"Calibration done: {pixel_per_mm:.2f} px/mm")

# --- Step 2: Object detection ---
def detect_objects(frame):
    results = model(frame, verbose=False)
    objects = []
    
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            name = model.names[cls]
            x1, y1, x2, y2 = box.xyxy[0]
            objects.append({
                "name": name,
                "box": [x1, y1, x2, y2]
            })
    return objects

# --- Step 3: Measure size in mm ---
def measure_objects(objects):
    if pixel_per_mm is None:
        print("Camera not calibrated!")
        return []
    
    measured = []
    for obj in objects:
        x1, y1, x2, y2 = obj["box"]
        width_mm = (x2 - x1) / pixel_per_mm
        height_mm = (y2 - y1) / pixel_per_mm
        measured.append({
            "name": obj["name"],
            "width_mm": width_mm,
            "height_mm": height_mm
        })
    return measured

# --- Step 4: Main loop ---
if __name__ == "__main__":
    calibrate_camera()
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        objects = detect_objects(frame)
        measured = measure_objects(objects)
        
        # Draw boxes and measurements
        for obj, m in zip(objects, measured):
            x1, y1, x2, y2 = map(int, obj["box"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{obj['name']} {m['width_mm']:.1f}x{m['height_mm']:.1f} mm",
                        (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imshow("Object Detection", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
            break
    
    cap.release()
    cv2.destroyAllWindows()
