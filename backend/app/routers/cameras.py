import csv, io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Camera
from ..schemas.camera import CameraCreate, CameraUpdate, CameraOut

router = APIRouter(prefix="/cameras", tags=["cameras"])

@router.get("", response_model=List[CameraOut])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).order_by(Camera.id).all()

@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    return cam

@router.post("", response_model=CameraOut, status_code=201)
def create_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    if db.query(Camera).filter_by(camera_code=payload.camera_code).first():
        raise HTTPException(409, f"camera_code '{payload.camera_code}' already exists")
    cam = Camera(**payload.model_dump())
    db.add(cam); db.commit(); db.refresh(cam)
    return cam

@router.patch("/{camera_id}", response_model=CameraOut)
def update_camera(camera_id: int, payload: CameraUpdate, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(cam, k, v)
    db.commit(); db.refresh(cam)
    return cam

@router.delete("/{camera_id}", status_code=204)
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    cam = db.get(Camera, camera_id)
    if not cam:
        raise HTTPException(404, "Camera not found")
    db.delete(cam); db.commit()

# ---- Bulk onboarding: upload a CSV matching data/sample_cameras.csv headers ----
@router.post("/bulk-upload")
def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    inserted, skipped, errors = 0, 0, []
    for i, row in enumerate(reader, start=2):  # row 1 is the header
        code = (row.get("camera_code") or "").strip()
        if not code:
            errors.append(f"row {i}: missing camera_code"); continue
        if db.query(Camera).filter_by(camera_code=code).first():
            skipped += 1; continue
        try:
            db.add(Camera(
                camera_code=code,
                name=(row.get("name") or code).strip(),
                department=(row.get("department") or "").strip() or None,
                camera_type=(row.get("camera_type") or "").strip() or None,
                rtsp_url=(row.get("rtsp_url") or "").strip(),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                status=(row.get("status") or "unknown").strip(),
            ))
            inserted += 1
        except Exception as e:
            errors.append(f"row {i}: {e}")
    db.commit()
    return {"inserted": inserted, "skipped_existing": skipped, "errors": errors}