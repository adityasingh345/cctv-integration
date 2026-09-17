"""
ANPR = find plate region -> OCR the text -> keep only plate-shaped strings.

Two modes:
  * If a license-plate YOLO model exists at PLATE_MODEL, use it to crop plates
    (accurate). Otherwise fall back to OCR-ing the whole frame (works, noisier).
"""
import os, re, cv2
import easyocr

# Loose Indian plate pattern e.g. UP78AB1234 (state + rto + series + number)
PLATE_RE = re.compile(r"[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{3,4}")

def norm_plate(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())

class ANPR:
    def __init__(self, plate_model=None, conf=0.3, gpu=False):
        plate_model = plate_model or os.getenv("PLATE_MODEL", "models/license_plate.pt")
        self.detector = None
        if os.path.exists(plate_model):
            try:
                from ultralytics import YOLO
                self.detector = YOLO(plate_model)
                print(f"[anpr] using plate detector: {plate_model}")
            except Exception as e:
                self.detector = None
                print(f"[anpr] plate model failed to load ({e}) -> OCR full frame")
        else:
            print("[anpr] no plate model found -> OCR full frame (less precise)")
        self.reader = easyocr.Reader(["en"], gpu=gpu)  # downloads model on first run
        self.conf = conf

    def _regions(self, frame):
        if self.detector:
            res = self.detector(frame, verbose=False, conf=self.conf)[0]
            return [[int(v) for v in b.xyxy[0].tolist()] for b in res.boxes]
        h, w = frame.shape[:2]
        return [[0, 0, w, h]]

    def read_plates(self, frame):
        """Return list of (plate_string, confidence)."""
        found = []
        for (x1, y1, x2, y2) in self._regions(frame):
            crop = frame[max(0, y1):y2, max(0, x1):x2]
            if crop.size == 0:
                continue
            for (_, text, prob) in self.reader.readtext(crop):
                plate = norm_plate(text)
                if PLATE_RE.search(plate):
                    found.append((plate, float(prob)))
        return found