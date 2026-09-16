import csv, io, re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Watchlist
from ..schemas.watchlist import WatchlistCreate, WatchlistOut

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

# Normalise plates so "up78 ab 1234" and "UP78AB1234" match the same way.
def norm_plate(p: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (p or "").upper())

@router.get("", response_model=List[WatchlistOut])
def list_watchlist(db: Session = Depends(get_db)):
    return db.query(Watchlist).order_by(Watchlist.id).all()

@router.post("", response_model=WatchlistOut, status_code=201)
def add_watch(payload: WatchlistCreate, db: Session = Depends(get_db)):
    plate = norm_plate(payload.plate_number)
    if db.query(Watchlist).filter_by(plate_number=plate).first():
        raise HTTPException(409, f"plate '{plate}' already on watchlist")
    data = payload.model_dump(); data["plate_number"] = plate
    w = Watchlist(**data)
    db.add(w); db.commit(); db.refresh(w)
    return w

@router.delete("/{watch_id}", status_code=204)
def remove_watch(watch_id: int, db: Session = Depends(get_db)):
    w = db.get(Watchlist, watch_id)
    if not w:
        raise HTTPException(404, "Watchlist entry not found")
    db.delete(w); db.commit()

@router.post("/bulk-upload")
def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    inserted, skipped = 0, 0
    for row in reader:
        plate = norm_plate(row.get("plate_number", ""))
        if not plate: continue
        if db.query(Watchlist).filter_by(plate_number=plate).first():
            skipped += 1; continue
        db.add(Watchlist(
            plate_number=plate,
            reason=(row.get("reason") or "").strip() or None,
            severity=(row.get("severity") or "medium").strip(),
            notes=(row.get("notes") or "").strip() or None,
        ))
        inserted += 1
    db.commit()
    return {"inserted": inserted, "skipped_existing": skipped}