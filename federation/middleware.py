"""
Federation middleware (Model 3).
Polls each mock VMS, normalizes via the per-vendor adapters, correlates
cross-system duplicates, and forwards to the EXISTING /detections/ingest.

It is just another client of your API — it changes nothing in the backend.
"""
import os, time, requests
from adapters.adapter_a import normalize as normalize_a
from adapters.adapter_b import normalize as normalize_b

VMS_A_URL = os.getenv("VMS_A_URL", "http://mock_vms_a:9001/events")
VMS_B_URL = os.getenv("VMS_B_URL", "http://mock_vms_b:9002/api/detections")
BACKEND   = os.getenv("BACKEND_URL", "http://backend:8000")
POLL_SEC  = int(os.getenv("POLL_SEC", "5"))
CORR_WINDOW = int(os.getenv("CORR_WINDOW_SEC", "10"))  # dedupe window

_recent = {}

def fetch(url):
    try:
        r = requests.get(url, timeout=5); r.raise_for_status(); return r.json()
    except Exception as e:
        print(f"[fed] fetch failed {url}: {e}"); return None

def correlate(det):
    """Return True if this detection is NEW (not a duplicate within the window)."""
    key = (det["plate_number"], det["camera_id"])
    now = time.time()
    last = _recent.get(key)
    _recent[key] = now
    if len(_recent) > 500:
        for k, t in list(_recent.items()):
            if now - t > CORR_WINDOW * 5:
                _recent.pop(k, None)
    return last is None or (now - last) > CORR_WINDOW

def forward(det):
    """POST a normalized detection into the existing backend."""
    try:
        requests.post(f"{BACKEND}/detections/ingest", json={
            "camera_id": det["camera_id"],
            "plate_number": det["plate_number"],
            "confidence": det["confidence"],
        }, timeout=5)
    except Exception as e:
        print(f"[fed] forward failed: {e}")

def cycle():
    detections = []
    a = fetch(VMS_A_URL)
    if a: detections += normalize_a(a)
    b = fetch(VMS_B_URL)
    if b: detections += normalize_b(b)

    forwarded, correlated = 0, 0
    for det in detections:
        if not det.get("plate_number") or det.get("camera_id") is None:
            continue
        if correlate(det):
            forward(det); forwarded += 1
        else:
            correlated += 1
            print(f"[fed] correlated duplicate: {det['plate_number']} "
                  f"@cam{det['camera_id']} (seen across systems)")
    if forwarded or correlated:
        print(f"[fed] cycle: {forwarded} forwarded, {correlated} correlated-out")

def main():
    print(f"[fed] federation middleware starting; polling every {POLL_SEC}s")
    print(f"[fed]   VMS A: {VMS_A_URL}")
    print(f"[fed]   VMS B: {VMS_B_URL}")
    print(f"[fed]   -> {BACKEND}/detections/ingest")
    while True:
        cycle()
        time.sleep(POLL_SEC)

if __name__ == "__main__":
    main()