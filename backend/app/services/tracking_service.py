## backend/app/services/tracking_service.py
import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from app.models.position import Position
from app.models.technician import Technician
from app.schemas.position import PositionCreate, PositionResponse
from app.services.traccar_service import TraccarService
from app.database import AsyncSessionLocal
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)


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


# ============================================================
# FUNÇÃO DE SINCRONIZAÇÃO COM O TRACCAR (COM BATERIA)
# ============================================================

async def update_all_technicians_positions():
    """Busca dispositivos no Traccar e atualiza técnicos no banco local."""
    print("🔍 Entrou na função de sincronização!")
    logger.info("🔄 Iniciando sincronização com Traccar...")
    traccar = TraccarService()
    
    print("🔍 Tentando autenticar no Traccar...")
    try:
        auth_ok = await traccar.authenticate()
        print(f"🔍 Autenticação retornou: {auth_ok}")
        logger.info(f"✅ Autenticação: {auth_ok}")
        if not auth_ok:
            print("❌ Falha na autenticação (retornou False)")
            logger.error("❌ Falha na autenticação com Traccar (retornou False)")
            return
    except Exception as e:
        print(f"❌ Exceção na autenticação: {e}")
        logger.error(f"❌ Exceção na autenticação: {e}")
        return

    print("🔍 Buscando dispositivos no Traccar...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{traccar.api_url}/devices",
                cookies={"JSESSIONID": traccar.session_cookie}
            )
            print(f"🔍 Status da resposta /devices: {response.status_code}")
            logger.info(f"📊 Status da requisição /devices: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Erro ao buscar dispositivos: {response.status_code}")
                logger.error(f"❌ Erro ao buscar dispositivos: {response.status_code}")
                return
            devices = response.json()
            print(f"🔍 Dispositivos encontrados: {len(devices)}")
            logger.info(f"📦 Dispositivos retornados: {len(devices)}")
            if not devices:
                print("⚠️ Nenhum dispositivo retornado pelo Traccar")
                logger.warning("⚠️ Nenhum dispositivo retornado pelo Traccar")
                return
        except Exception as e:
            print(f"❌ Exceção na requisição: {e}")
            logger.error(f"❌ Exceção na requisição: {e}")
            return

    print("🔍 Conectando ao banco de dados local...")
    async with AsyncSessionLocal() as db:
        print("🔍 Buscando técnicos ativos...")
        stmt = select(Technician).where(Technician.deleted_at.is_(None))
        result = await db.execute(stmt)
        technicians = result.scalars().all()
        print(f"🔍 Técnicos ativos encontrados: {len(technicians)}")
        logger.info(f"👤 Técnicos ativos encontrados: {len(technicians)}")

        updated_count = 0
        now = datetime.utcnow()

        for tech in technicians:
            if not tech.device_id:
                print(f"⏭️ Técnico {tech.name} (ID {tech.id}) sem device_id, ignorado")
                logger.debug(f"⏭️ Técnico {tech.name} sem device_id, ignorado")
                continue

            print(f"🔍 Processando técnico: {tech.name} (device_id: {tech.device_id})")
            # Encontra dispositivo correspondente
            device = next((d for d in devices if str(d.get("id")) == tech.device_id), None)
            if not device:
                print(f"⏭️ Técnico {tech.name} (device_id {tech.device_id}) não encontrado no Traccar")
                logger.debug(f"⏭️ Técnico {tech.name} (device_id {tech.device_id}) não encontrado no Traccar")
                continue

            print(f"🔍 Dispositivo encontrado: {device.get('name')} (ID: {device.get('id')})")

            # Busca a posição mais recente do dispositivo
            position = None
            async with httpx.AsyncClient() as client:
                pos_response = await client.get(
                    f"{traccar.api_url}/positions?deviceId={device['id']}&limit=1",
                    cookies={"JSESSIONID": traccar.session_cookie}
                )
                if pos_response.status_code == 200:
                    positions = pos_response.json()
                    if positions:
                        position = positions[0]  # Última posição

            # Converte lastUpdate para datetime naive
            last_update_str = device.get("lastUpdate")
            if last_update_str:
                try:
                    if last_update_str.endswith('Z'):
                        last_update_str = last_update_str[:-1] + '+00:00'
                    last_seen_dt = datetime.fromisoformat(last_update_str)
                    tech.last_seen = last_seen_dt.replace(tzinfo=None)
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Erro ao converter lastUpdate para {tech.name}: {e}")
                    tech.last_seen = None
            else:
                tech.last_seen = None

            # Define online se a última posição for recente (≤ 30 minutos)
            if tech.last_seen:
                seconds_since = (now - tech.last_seen).total_seconds()
                tech.is_online = seconds_since < 1800  # 30 minutos
                print(f"🔍 Última posição: {tech.last_seen} ({seconds_since:.0f}s atrás), online: {tech.is_online}")
            else:
                tech.is_online = False
                print("🔍 Sem last_seen, definido como offline")

            # Atualiza posição e bateria a partir da posição buscada
            if position:
                tech.latitude = position.get("latitude")
                tech.longitude = position.get("longitude")
                tech.accuracy = position.get("accuracy")
                # Bateria está dentro de 'attributes'
                attributes = position.get("attributes", {})
                battery = attributes.get("batteryLevel") or attributes.get("battery")
                if battery is not None:
                    tech.battery_level = battery
                    print(f"🔋 {tech.name} - Bateria: {battery}%")
                else:
                    print(f"⚠️ Bateria não disponível para {tech.name}")
                print(f"📍 Posição atualizada: ({tech.latitude}, {tech.longitude})")
            else:
                print(f"⚠️ Sem posição para {tech.name} (positionId: {device.get('positionId')})")

            updated_count += 1
            print(f"✅ Técnico {tech.name} atualizado com sucesso!")

        await db.commit()
        print(f"✅ Sincronização concluída: {updated_count} técnicos atualizados")
        logger.info(f"✅ Sincronização concluída: {updated_count} técnicos atualizados")