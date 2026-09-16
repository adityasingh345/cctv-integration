from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, func
from ..database import Base

class Alert(Base):
    __tablename__ = "alerts"
    id            = Column(BigInteger, primary_key=True)
    detection_id  = Column(BigInteger, ForeignKey("detections.id"))
    watchlist_id  = Column(Integer, ForeignKey("watchlist.id"))
    camera_id     = Column(Integer, ForeignKey("cameras.id"))
    plate_number  = Column(String(32))
    reason        = Column(String(128))
    severity      = Column(String(32))
    acknowledged  = Column(Boolean, default=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())