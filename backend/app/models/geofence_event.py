from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer
from datetime import datetime
from app.database import Base
import uuid

class GeofenceEvent(Base):
    __tablename__ = "geofence_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(Integer, nullable=False, index=True)  # ID do dispositivo no Traccar
    geofence_id = Column(String, ForeignKey("geofences.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # 'enter' ou 'exit'
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    duration_seconds = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<GeofenceEvent device={self.device_id} geofence={self.geofence_id} type={self.event_type}>"