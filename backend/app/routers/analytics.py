from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Detection, Camera

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """Overall vehicle metadata: totals, breakdown by type, by camera."""
    total = db.query(Detection).count()

    type_rows = (db.query(Detection.object_type, func.count())
                   .group_by(Detection.object_type).all())
    by_type = {(t or "unknown"): c for t, c in type_rows}

    cam_rows = (db.query(Camera.camera_code, func.count(Detection.id))
                  .join(Detection, Detection.camera_id == Camera.id)
                  .group_by(Camera.camera_code).all())
    by_camera = {code: c for code, c in cam_rows}

    with_plate = db.query(Detection).filter(Detection.plate_number.isnot(None),
                                             Detection.plate_number != "").count()
    return {
        "total_vehicles": total,
        "by_type": by_type,
        "by_camera": by_camera,
        "with_plate": with_plate,
        "without_plate": total - with_plate,
    }

@router.get("/per-minute")
def per_minute(db: Session = Depends(get_db)):
    """Vehicle detections per minute (for a traffic-flow chart)."""
    minute = func.date_trunc("minute", Detection.detected_at)
    rows = (db.query(minute.label("m"), func.count().label("c"))
              .group_by("m").order_by("m").all())
    return [{"minute": m.isoformat() if m else None, "count": c} for m, c in rows][-30:]

@router.get("/rate")
def rate(db: Session = Depends(get_db)):
    """Average vehicles per minute + latest minute's count."""
    minute = func.date_trunc("minute", Detection.detected_at)
    rows = db.query(minute.label("m"), func.count().label("c")).group_by("m").all()
    if not rows:
        return {"avg_per_minute": 0, "latest_minute_count": 0, "minutes_tracked": 0}
    counts = [c for _, c in rows]
    return {
        "avg_per_minute": round(sum(counts) / len(counts), 1),
        "latest_minute_count": counts[-1],
        "minutes_tracked": len(counts),
    }