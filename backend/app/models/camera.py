from sqlalchemy import Column, Integer, String, Float, DateTime, func
from geoalchemy2 import Geometry
from ..database import Base

class Camera(Base):
    __tablename__ = "cameras"
    id          = Column(Integer, primary_key=True)
    camera_code = Column(String(64), unique=True, nullable=False)
    name        = Column(String(255), nullable=False)
    department  = Column(String(128))
    camera_type = Column(String(64))
    rtsp_url    = Column(String, nullable=False)
    latitude    = Column(Float, nullable=False)
    longitude   = Column(Float, nullable=False)
    # geom is auto-filled by a DB trigger from lat/long -> we never set it here.
    geom        = Column(Geometry("POINT", srid=4326))
    status      = Column(String(32), default="unknown")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())