from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, ForeignKey, func
from ..database import Base

class Detection(Base):
    __tablename__ = "detections"
    id            = Column(BigInteger, primary_key=True)
    camera_id     = Column(Integer, ForeignKey("cameras.id"))
    plate_number  = Column(String(32))
    object_type   = Column(String(32), default="vehicle")
    confidence    = Column(Float)
    snapshot_path = Column(String)
    detected_at   = Column(DateTime(timezone=True), server_default=func.now())