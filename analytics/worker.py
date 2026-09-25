"""
Analytics worker: for each onboarded camera, open its RTSP stream, sample
frames, run vehicle detection + ANPR, and POST every plate sighting to the
backend as a detection. One thread per camera; a shared lock serialises the
(GPU/CPU) model calls so a small machine stays stable.
"""
import os, time, threading, requests, cv2
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
from detector import VehicleDetector
from anpr import ANPR, norm_plate
import subprocess, numpy as np
from urllib.parse import urlparse, unquote

BACKEND      = os.getenv("BACKEND_URL", "http://backend:8000")
SAMPLE_EVERY = int(os.getenv("FRAME_SAMPLE_EVERY", "5"))   # analyse every Nth frame
SNAP_DIR     = os.getenv("SNAPSHOT_DIR", "/snapshots")
MAX_CAMERAS  = int(os.getenv("MAX_CAMERAS", "10"))         # cap live analysis on a laptop
YOLO_MODEL   = os.getenv("YOLO_MODEL", "yolov8n.pt")

os.makedirs(SNAP_DIR, exist_ok=True)

detector = VehicleDetector(YOLO_MODEL)
anpr     = ANPR()
lock     = threading.Lock()      # models are shared -> one inference at a time

def _read_exact(stream, n):
    buf = b""
    while len(buf) < n:
        chunk = stream.read(n - len(buf))
        if not chunk:
            return buf        # stream ended
        buf += chunk
    return buf

def build_capture(raw_url):
    p = urlparse(raw_url)
    user = unquote(p.username or "")   # decode %40 -> @
    pwd  = unquote(p.password or "")
    host = p.hostname or ""
    port = f":{p.port}" if p.port else ""
    # FFmpeg accepts credentials before host; the decoded '@' in the email is
    # fine because FFmpeg splits on the LAST '@' before the host.
    return f"rtsp://{user}:{pwd}@{host}{port}{p.path}"

def get_cameras():
    """Wait for the backend + registry, then return the camera list."""
    while True:
        try:
            r = requests.get(f"{BACKEND}/cameras", timeout=10)
            r.raise_for_status()
            cams = r.json()
            if cams:
                return cams
            print("[worker] no cameras onboarded yet; retrying in 5s...")
        except Exception as e:
            print(f"[worker] backend not ready ({e}); retrying in 5s...")
        time.sleep(5)

def post_detection(payload):
    try:
        requests.post(f"{BACKEND}/detections/ingest", json=payload, timeout=5)
    except Exception as e:
        print(f"[worker] post failed: {e}")

def process_camera(cam):
    url, cid, code = cam["rtsp_url"], cam["id"], cam["camera_code"]
    print(f"[worker] {code}: opening {url}")
    cap = cv2.VideoCapture(url)
    n = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            print(f"[worker] {code}: stream drop, reconnecting...")
            cap.release(); time.sleep(2); cap = cv2.VideoCapture(url); continue
        n += 1
        if n % SAMPLE_EVERY:
            continue

        with lock:
            vehicles = detector.detect(frame)      # [(box, type, conf), ...]
            plates   = anpr.read_plates(frame)      # [(plate, conf), ...] may be empty

        # 1. Log every vehicle with its TYPE (works even if plate unreadable)
        for (box, vtype, vconf) in vehicles:
            post_detection({
                "camera_id": cid,
                "plate_number": None,             # no plate needed for metadata
                "object_type": vtype,             # car / truck / bus / motorcycle
                "confidence": round(vconf, 3),
                "snapshot_path": None,
            })

        # 2. If any plate WAS readable, log it too (bonus when quality allows)
        for plate, prob in plates:
            post_detection({
                "camera_id": cid,
                "plate_number": plate,
                "object_type": "vehicle",
                "confidence": round(prob, 3),
                "snapshot_path": None,
            })

        if vehicles:
            counts = {}
            for (_, vt, _) in vehicles:
                counts[vt] = counts.get(vt, 0) + 1
            print(f"[worker] {code}: {counts}" + (f" | plates: {[p for p,_ in plates]}" if plates else ""))

def main():
    cams = get_cameras()[:MAX_CAMERAS]
    print(f"[worker] analysing {len(cams)} camera(s)")
    threads = []
    for cam in cams:
        t = threading.Thread(target=process_camera, args=(cam,), daemon=True)
        t.start(); threads.append(t); time.sleep(0.5)
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()