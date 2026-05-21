from sqlalchemy import Column, String, DateTime, JSON, Text, Integer
from datetime import datetime
from app.database import Base
import uuid


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Referências
    technician_id = Column(String, nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    geofence_id = Column(String, nullable=True, index=True)
    
    # Tipo de evento
    event_type = Column(String, nullable=False, index=True)  # 
    # geofence_enter, geofence_exit, online, offline, battery_low, 
    # speed_threshold, movement_started, movement_stopped, etc
    
    # Descrição
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Dados contextuais
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    event_timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Event id={self.id} type={self.event_type} timestamp={self.event_timestamp}>"
