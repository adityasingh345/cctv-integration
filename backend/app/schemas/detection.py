from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DetectionIngest(BaseModel):
    camera_id: Optional[int] = None
    plate_number: Optional[str] = None
    object_type: Optional[str] = "vehicle"
    confidence: Optional[float] = None
    snapshot_path: Optional[str] = None

class DetectionOut(DetectionIngest):
    id: int
    detected_at: Optional[datetime] = None
    class Config:
        from_attributes = True