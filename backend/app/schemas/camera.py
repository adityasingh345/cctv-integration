from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CameraBase(BaseModel):
    camera_code: str
    name: str
    department: Optional[str] = None
    camera_type: Optional[str] = None
    rtsp_url: str
    latitude: float
    longitude: float
    status: Optional[str] = "unknown"

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    camera_type: Optional[str] = None
    rtsp_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[str] = None

class CameraOut(CameraBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True