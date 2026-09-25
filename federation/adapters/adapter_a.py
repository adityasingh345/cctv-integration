"""
Adapter for Vendor A.
Input  (Vendor A): {"vendor":"A","events":[{"cam","plate","score","ts"}]}
Output (standard): [{"camera_id","plate_number","confidence","source"}]
"""
from .camera_map import resolve

def normalize(payload: dict):
    out = []
    for e in payload.get("events", []):          # A wraps events in an object
        cam_id = resolve(e.get("cam"))           # A-02 -> registry id
        if cam_id is None:
            continue
        out.append({
            "camera_id": cam_id,
            "plate_number": e.get("plate"),       # 'plate' -> 'plate_number'
            "confidence": float(e.get("score", 0)),  # already 0-1
            "source": "vms_a",                    # tag where it came from
        })
    return out