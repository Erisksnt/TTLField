from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, unique=True, nullable=False, index=True)  # UUID do app
    imei = Column(String, unique=True, nullable=True, index=True)
    
    # Informações do dispositivo
    device_name = Column(String, nullable=False)
    device_model = Column(String, nullable=True)
    os_type = Column(String, nullable=False)  # Android, iOS
    os_version = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_tracking = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, nullable=True)
    
    # Configurações de rastreamento
    tracking_interval = Column(Integer, default=30)  # segundos
    battery_saver_enabled = Column(Boolean, default=True)
    adaptive_tracking = Column(Boolean, default=True)
    
    # Status da conexão
    app_version = Column(String, nullable=True)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Notas
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Device id={self.id} model={self.device_model} os={self.os_type}>"