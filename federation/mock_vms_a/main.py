"""
Mock VMS 'Vendor A'. Pretends to be a departmental VMS platform.
Exposes GET /events returning plate sightings in VENDOR A's format.
This stands in for a real vendor VMS (Milestone, Genetec, etc.).
"""
import random, time
from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI(title="Mock VMS A (Vendor X)")

# Vendor A labels its cameras A-01.. and uses these field names.
CAMERAS_A = ["A-01", "A-02", "A-03"]
PLATES = ["MH12AB1234", "DL01CX9988", "UP78AB1234", "KA05MN4321", "RJ14PQ7788"]

@app.get("/events")
def events():
    """Vendor A shape: {'events': [{'cam','plate','score','ts'}]}"""
    out = []
    for _ in range(random.randint(1, 3)):
        out.append({
            "cam": random.choice(CAMERAS_A),
            "plate": random.choice(PLATES),
            "score": round(random.uniform(0.6, 0.98), 2),
            "ts": datetime.now(timezone.utc).isoformat(),
        })
    return {"vendor": "A", "events": out}

@app.get("/health")
def health():
    return {"status": "ok", "vendor": "A"}