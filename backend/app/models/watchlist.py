from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from ..database import Base

class Watchlist(Base):
    __tablename__ = "watchlist"
    id           = Column(Integer, primary_key=True)
    plate_number = Column(String(32), unique=True, nullable=False)
    reason       = Column(String(128))
    severity     = Column(String(32), default="medium")
    notes        = Column(Text)
    active       = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())