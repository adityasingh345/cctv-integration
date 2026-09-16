from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WatchlistBase(BaseModel):
    plate_number: str
    reason: Optional[str] = None
    severity: Optional[str] = "medium"
    notes: Optional[str] = None
    active: Optional[bool] = True

class WatchlistCreate(WatchlistBase):
    pass

class WatchlistOut(WatchlistBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True