from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer
from datetime import datetime
from app.database import Base
import uuid


class Geofence(Base):
    __tablename__ = "geofences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Tipo de geofence
    geofence_type = Column(String, nullable=False)  # circle, polygon, rectangle
    
    # Dados geométricos (GeoJSON ou coordenadas)
    geometry = Column(JSON, nullable=False)
    
    # Para círculos
    center_latitude = Column(String, nullable=True)
    center_longitude = Column(String, nullable=True)
    radius = Column(Integer, nullable=True)  # metros
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Alertas associados
    alert_on_enter = Column(Boolean, default=True)
    alert_on_exit = Column(Boolean, default=True)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    # events = relationship("Event", back_populates="geofence", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Geofence id={self.id} name={self.name} type={self.geofence_type}>"