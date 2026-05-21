from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, ForeignKey
from datetime import datetime
from app.database import Base
import uuid


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Referências
    technician_id = Column(String, nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    geofence_id = Column(String, ForeignKey("geofences.id"), nullable=True)
    
    # Tipo de alerta
    alert_type = Column(String, nullable=False, index=True)  # 
    # speeding, offline, geofence_exit, geofence_enter, low_battery, stationary, 
    # movement_detected, etc
    
    # Descrição
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Severity: low, medium, high, critical
    severity = Column(String, default="medium")
    
    # Status
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String, nullable=True)
    
    # Dados adicionais
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Alert id={self.id} type={self.alert_type} severity={self.severity}>"
