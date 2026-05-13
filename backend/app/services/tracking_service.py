from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from app.models.position import Position
from app.models.technician import Technician
from app.schemas.position import PositionCreate, PositionResponse
from math import radians, cos, sin, asin, sqrt


class TrackingService:
    @staticmethod
    def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """
        Calcular distância entre dois pontos lat/lon em metros
        Fórmula haversine
        """
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Raio da Terra em metros
        return c * r

    @staticmethod
    async def create_position(
        db: AsyncSession,
        technician_id: str,
        device_id: str,
        position: PositionCreate,
    ) -> Position:
        """Criar nova posição e atualizar status do técnico"""
        db_position = Position(
            technician_id=technician_id,
            device_id=device_id,
            latitude=position.latitude,
            longitude=position.longitude,
            accuracy=position.accuracy,
            altitude=position.altitude,
            speed=position.speed,
            heading=position.heading,
            battery_level=position.battery_level,
            battery_status=position.battery_status,
            provider=position.provider,
            timestamp=datetime.utcnow(),
        )
        
        db.add(db_position)
        
        # Atualizar localização do técnico
        stmt = select(Technician).where(Technician.id == technician_id)
        result = await db.execute(stmt)
        technician = result.scalar_one_or_none()
        
        if technician:
            technician.latitude = position.latitude
            technician.longitude = position.longitude
            technician.accuracy = position.accuracy
            technician.battery_level = position.battery_level
            technician.last_seen = datetime.utcnow()
            technician.is_online = True
        
        await db.commit()
        await db.refresh(db_position)
        return db_position

    @staticmethod
    async def get_technician_positions(
        db: AsyncSession,
        technician_id: str,
        hours: int = 24,
        limit: int = 1000,
    ) -> list[PositionResponse]:
        """Obter histórico de posições do técnico"""
        time_ago = datetime.utcnow() - timedelta(hours=hours)
        
        stmt = (
            select(Position)
            .where(
                and_(
                    Position.technician_id == technician_id,
                    Position.timestamp >= time_ago,
                )
            )
            .order_by(desc(Position.timestamp))
            .limit(limit)
        )
        
        result = await db.execute(stmt)
        positions = result.scalars().all()
        return [PositionResponse.model_validate(p) for p in positions]

    @staticmethod
    async def get_all_technicians_current_position(
        db: AsyncSession,
    ) -> list[dict]:
        """Obter posição atual de todos os técnicos online"""
        stmt = (
            select(Technician)
            .where(Technician.is_online == True)
            .order_by(Technician.name)
        )
        
        result = await db.execute(stmt)
        technicians = result.scalars().all()
        
        return [
            {
                "id": t.id,
                "name": t.name,
                "latitude": t.latitude,
                "longitude": t.longitude,
                "accuracy": t.accuracy,
                "battery_level": t.battery_level,
                "last_seen": t.last_seen,
                "is_online": t.is_online,
            }
            for t in technicians
        ]

    @staticmethod
    async def calculate_route_distance(
        db: AsyncSession,
        technician_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Calcular distância total percorrida num período"""
        stmt = (
            select(Position)
            .where(
                and_(
                    Position.technician_id == technician_id,
                    Position.timestamp >= start_time,
                    Position.timestamp <= end_time,
                )
            )
            .order_by(Position.timestamp)
        )
        
        result = await db.execute(stmt)
        positions = result.scalars().all()
        
        if len(positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(positions) - 1):
            curr = positions[i]
            next_pos = positions[i + 1]
            distance = TrackingService.haversine(
                curr.longitude,
                curr.latitude,
                next_pos.longitude,
                next_pos.latitude,
            )
            total_distance += distance
        
        return total_distance / 1000  # Converter para km