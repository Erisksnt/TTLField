## backend/app/services/position_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.position import Position
from datetime import datetime
import uuid


class PositionService:
    """Serviço para gerenciar posições de técnicos"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def save_position(self, technician_id: str, **kwargs):
        """Salvar posição do técnico no banco de dados"""
        position = Position(
            id=str(uuid.uuid4()),
            technician_id=technician_id,
            latitude=kwargs.get("latitude"),
            longitude=kwargs.get("longitude"),
            accuracy=kwargs.get("accuracy"),
            speed=kwargs.get("speed"),
            heading=kwargs.get("heading"),
            battery_level=kwargs.get("battery_level"),
            timestamp=kwargs.get("timestamp", datetime.utcnow()),
            received_at=datetime.utcnow()
        )
        self.db.add(position)
        await self.db.commit()
        return position