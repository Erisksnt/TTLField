from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey, Index
from datetime import datetime
from app.database import Base
import uuid
from sqlalchemy import Boolean


class Position(Base):
    __tablename__ = "positions"
    
    __table_args__ = (
        Index('idx_technician_timestamp', 'technician_id', 'timestamp'),
        Index('idx_device_timestamp', 'device_id', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Referências
    technician_id = Column(String, nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    
    # Coordenadas GPS
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    
    # Movimento
    speed = Column(Float, nullable=True)  # km/h
    heading = Column(Float, nullable=True)  # graus
    
    # Dispositivo
    battery_level = Column(Integer, nullable=True)  # 0-100
    battery_status = Column(String, nullable=True)  # charging, discharging
    
    # Provedor de localização
    provider = Column(String, default="gps")  # gps, network, fused
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Qualidade de sinal
    is_valid = Column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<Position id={self.id} tech={self.technician_id} lat={self.latitude} lon={self.longitude}>"
