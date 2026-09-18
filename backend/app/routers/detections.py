import json
import redis
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..config import settings
from ..models import Detection, Alert, Camera
from ..schemas.detection import DetectionIngest, DetectionOut
from ..matching import find_match, norm_plate

router = APIRouter(prefix="/detections", tags=["detections"])

# sync client used only to publish alert events to the WS bridge
_redis = redis.from_url(settings.REDIS_URL)

@router.post("/ingest", response_model=DetectionOut, status_code=201)
def ingest(payload: DetectionIngest, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["plate_number"] = norm_plate(data.get("plate_number"))
    det = Detection(**data)
    db.add(det); db.commit(); db.refresh(det)

    # --- watchlist matching ---
    match = find_match(det.plate_number, db)
    if match:
        w, score = match
        alert = Alert(
            detection_id=det.id,
            watchlist_id=w.id,
            camera_id=det.camera_id,
            plate_number=det.plate_number,
            reason=w.reason,
            severity=w.severity,
        )
        db.add(alert); db.commit(); db.refresh(alert)

        # enrich with camera location for the map popup, then push live
        cam = db.get(Camera, det.camera_id) if det.camera_id else None
        event = {
            "id": alert.id,
            "plate_number": alert.plate_number,
            "matched_plate": w.plate_number,
            "match_score": round(score, 2),
            "reason": alert.reason,
            "severity": alert.severity,
            "camera_id": alert.camera_id,
            "camera_code": cam.camera_code if cam else None,
            "latitude": cam.latitude if cam else None,
            "longitude": cam.longitude if cam else None,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
        try:
            _redis.publish("alerts", json.dumps(event))
        except Exception as e:
            print(f"[ingest] redis publish failed: {e}")
    return det

@router.get("", response_model=List[DetectionOut])
def list_detections(plate: Optional[str] = None, limit: int = 100,
                    db: Session = Depends(get_db)):
    q = db.query(Detection)
    if plate:
        q = q.filter(Detection.plate_number == norm_plate(plate))
    return q.order_by(Detection.detected_at.desc()).limit(limit).all()