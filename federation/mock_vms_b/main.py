"""
Mock VMS 'Vendor B'. A SECOND departmental VMS with a DIFFERENT API shape,
to prove the adapter/federation pattern across heterogeneous vendors.
Exposes GET /api/detections in VENDOR B's format (different field names!).
"""
import random
from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI(title="Mock VMS B (Vendor Y)")

# Vendor B labels cameras differently and uses different field names + units.
DEVICES_B = ["CAM_B_7", "CAM_B_8", "CAM_B_9"]
PLATES = ["MH12AB1234", "DL01CX9988", "MP09ZZ0001", "GJ01AA1111", "UP78AB1234"]

@app.get("/api/detections")
def detections():
    """Vendor B shape: a bare list of {'device_id','detected_plate','confidence_pct','time'}"""
    out = []
    for _ in range(random.randint(1, 3)):
        out.append({
            "device_id": random.choice(DEVICES_B),
            "detected_plate": random.choice(PLATES),
            "confidence_pct": random.randint(60, 98),   # 0-100, not 0-1!
            "time": datetime.now(timezone.utc).isoformat(),
        })
    return out

@app.get("/health")
def health():
    return {"status": "ok", "vendor": "B"}