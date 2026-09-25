"""
Adapter for Vendor B.
Input  (Vendor B): [{"device_id","detected_plate","confidence_pct","time"}]  (bare list)
Output (standard): [{"camera_id","plate_number","confidence","source"}]
"""
from .camera_map import resolve

def normalize(payload: list):
    out = []
    for e in payload:                             # B is already a bare list
        cam_id = resolve(e.get("device_id"))      # CAM_B_9 -> registry id
        if cam_id is None:
            continue
        out.append({
            "camera_id": cam_id,
            "plate_number": e.get("detected_plate"),        # different field name
            "confidence": float(e.get("confidence_pct", 0)) / 100.0,  # 63 -> 0.63
            "source": "vms_b",
        })
    return out