from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    cpf = Column(String, unique=True, nullable=True, index=True)
    
    # Status operacional
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, nullable=True)
    
    # Localização atual (cache)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    
    # Status do dispositivo
    battery_level = Column(Integer, nullable=True)  # 0-100
    device_id = Column(String, ForeignKey("devices.id"), nullable=True)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Notas
    notes = Column(Text, nullable=True)
    
    # Relacionamentos
    # device = relationship("Device", back_populates="technician")
    # positions = relationship("Position", back_populates="technician", cascade="all, delete-orphan")
    # events = relationship("Event", back_populates="technician", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Technician id={self.id} name={self.name} online={self.is_online}>"
