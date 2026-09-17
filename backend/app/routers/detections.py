import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Detection
from ..schemas.detection import DetectionIngest, DetectionOut

router = APIRouter(prefix="/detections", tags=["detections"])

def norm_plate(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())

# The analytics worker POSTs every plate sighting here.
# (Phase 5 will extend this to match the watchlist and raise alerts.)
@router.post("/ingest", response_model=DetectionOut, status_code=201)
def ingest(payload: DetectionIngest, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["plate_number"] = norm_plate(data.get("plate_number"))
    det = Detection(**data)
    db.add(det); db.commit(); db.refresh(det)
    return det

@router.get("", response_model=List[DetectionOut])
def list_detections(plate: Optional[str] = None, limit: int = 100,
                    db: Session = Depends(get_db)):
    q = db.query(Detection)
    if plate:
        q = q.filter(Detection.plate_number == norm_plate(plate))
    return q.order_by(Detection.detected_at.desc()).limit(limit).all()