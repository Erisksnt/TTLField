## backend/app/models/audit_log.py
from sqlalchemy import Column, String, DateTime, Text, JSON
from app.database import Base
from datetime import datetime


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)  # Quem fez a ação
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    resource = Column(String, nullable=False)  # technician, geofence, user, etc
    resource_id = Column(String, nullable=True)  # ID do recurso afetado
    old_data = Column(JSON, nullable=True)  # Estado anterior (para updates)
    new_data = Column(JSON, nullable=True)  # Estado novo
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)