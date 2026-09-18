from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertOut(BaseModel):
    id: int
    detection_id: Optional[int] = None
    watchlist_id: Optional[int] = None
    camera_id: Optional[int] = None
    plate_number: Optional[str] = None
    reason: Optional[str] = None
    severity: Optional[str] = None
    acknowledged: bool = False
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True