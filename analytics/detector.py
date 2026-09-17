"""YOLOv8 vehicle detector. Uses the standard COCO model (auto-downloads)."""
from ultralytics import YOLO

# COCO class ids that count as vehicles
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

class VehicleDetector:
    def __init__(self, model_path="yolov8n.pt", conf=0.4):
        self.model = YOLO(model_path)     # downloads yolov8n.pt on first use
        self.conf = conf

    def detect(self, frame):
        """Return [(x1,y1,x2,y2), class_name, confidence] for each vehicle."""
        res = self.model(frame, verbose=False, conf=self.conf)[0]
        out = []
        for b in res.boxes:
            cls = int(b.cls[0])
            if cls in VEHICLE_CLASSES:
                xyxy = [int(v) for v in b.xyxy[0].tolist()]
                out.append((xyxy, VEHICLE_CLASSES[cls], float(b.conf[0])))
        return out