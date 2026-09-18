from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Camera, Detection, Alert, Watchlist

router = APIRouter(tags=["meta"])

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return {
        "cameras": db.query(Camera).count(),
        "detections": db.query(Detection).count(),
        "alerts": db.query(Alert).count(),
        "watchlist": db.query(Watchlist).count(),
    }