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
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371000
        return c * r

    @staticmethod
    async def create_position(db, technician_id, device_id, position):
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
    async def get_technician_positions(db, technician_id, hours=24, limit=1000):
        time_ago = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(Position)
            .where(and_(Position.technician_id == technician_id, Position.timestamp >= time_ago))
            .order_by(desc(Position.timestamp))
            .limit(limit)
        )
        result = await db.execute(stmt)
        positions = result.scalars().all()
        return [PositionResponse.model_validate(p) for p in positions]

    @staticmethod
    async def get_all_technicians_current_position(db):
        stmt = select(Technician).where(Technician.is_online == True).order_by(Technician.name)
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
    async def calculate_route_distance(db, technician_id, start_time, end_time):
        stmt = (
            select(Position)
            .where(and_(Position.technician_id == technician_id, Position.timestamp >= start_time, Position.timestamp <= end_time))
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
            distance = TrackingService.haversine(curr.longitude, curr.latitude, next_pos.longitude, next_pos.latitude)
            total_distance += distance
        return total_distance / 1000


async def update_all_technicians_positions():
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
            response = await client.get(f"{traccar.api_url}/devices", cookies={"JSESSIONID": traccar.session_cookie})
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
        positions_saved = 0
        now = datetime.utcnow()

        for tech in technicians:
            if not tech.device_id:
                print(f"⏭️ Técnico {tech.name} (ID {tech.id}) sem device_id, ignorado")
                logger.debug(f"⏭️ Técnico {tech.name} sem device_id, ignorado")
                continue

            print(f"🔍 Processando técnico: {tech.name} (device_id: {tech.device_id})")
            device = next((d for d in devices if str(d.get("id")) == tech.device_id), None)
            if not device:
                print(f"⏭️ Técnico {tech.name} (device_id {tech.device_id}) não encontrado no Traccar")
                logger.debug(f"⏭️ Técnico {tech.name} (device_id {tech.device_id}) não encontrado no Traccar")
                continue

            print(f"🔍 Dispositivo encontrado: {device.get('name')} (ID: {device.get('id')})")

            # Busca posição mais recente
            position = None
            async with httpx.AsyncClient() as client:
                pos_response = await client.get(
                    f"{traccar.api_url}/positions?deviceId={device['id']}&limit=1",
                    cookies={"JSESSIONID": traccar.session_cookie}
                )
                if pos_response.status_code == 200:
                    positions_list = pos_response.json()
                    if positions_list:
                        position = positions_list[0]

            # Atualiza last_seen e online
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

            if tech.last_seen:
                seconds_since = (now - tech.last_seen).total_seconds()
                tech.is_online = seconds_since < 1800
                print(f"🔍 Última posição: {tech.last_seen} ({seconds_since:.0f}s atrás), online: {tech.is_online}")
            else:
                tech.is_online = False
                print("🔍 Sem last_seen, definido como offline")

            # Atualiza dados do técnico e salva posição (se nova)
            if position:
                tech.latitude = position.get("latitude")
                tech.longitude = position.get("longitude")
                tech.accuracy = position.get("accuracy")
                attributes = position.get("attributes", {})
                battery = attributes.get("batteryLevel") or attributes.get("battery")
                if battery is not None:
                    tech.battery_level = battery
                    print(f"🔋 {tech.name} - Bateria: {battery}%")
                else:
                    print(f"⚠️ Bateria não disponível para {tech.name}")
                print(f"📍 Posição atualizada: ({tech.latitude}, {tech.longitude})")

                # Prepara timestamp
                pos_timestamp = position.get("fixTime") or position.get("serverTime") or datetime.utcnow()
                if isinstance(pos_timestamp, str):
                    pos_timestamp = datetime.fromisoformat(pos_timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
                elif isinstance(pos_timestamp, datetime) and pos_timestamp.tzinfo is not None:
                    pos_timestamp = pos_timestamp.replace(tzinfo=None)

                # 🔥 VERIFICA SE JÁ EXISTE POSIÇÃO COM ESTE TIMESTAMP PARA ESTE TÉCNICO
                existing_stmt = select(Position).where(
                    and_(
                        Position.technician_id == tech.id,
                        Position.timestamp == pos_timestamp
                    )
                )
                existing_result = await db.execute(existing_stmt)
                if existing_result.scalar_one_or_none():
                    print(f"⏭️ Posição já existe para {tech.name} em {pos_timestamp} (ignorando duplicata)")
                else:
                    # Salva posição (nova)
                    speed_ms = position.get("speed")
                    speed_kmh = speed_ms * 3.6 if speed_ms is not None else None
                    new_position = Position(
                        technician_id=tech.id,
                        device_id=tech.device_id,
                        latitude=position.get("latitude"),
                        longitude=position.get("longitude"),
                        accuracy=position.get("accuracy"),
                        altitude=position.get("altitude"),
                        speed=speed_kmh,
                        heading=position.get("course"),
                        battery_level=battery,
                        battery_status=attributes.get("batteryStatus"),
                        provider=position.get("protocol", "traccar"),
                        timestamp=pos_timestamp,
                        received_at=datetime.utcnow(),
                        is_valid=position.get("valid", True),
                    )
                    db.add(new_position)
                    positions_saved += 1
                    print(f"💾 Posição salva para {tech.name} (timestamp: {pos_timestamp})")
            else:
                print(f"⚠️ Sem posição para {tech.name} (positionId: {device.get('positionId')})")

            updated_count += 1
            print(f"✅ Técnico {tech.name} atualizado com sucesso!")

        await db.commit()
        print(f"✅ Sincronização concluída: {updated_count} técnicos atualizados, {positions_saved} posições salvas")
        logger.info(f"✅ Sincronização concluída: {updated_count} técnicos atualizados, {positions_saved} posições salvas")