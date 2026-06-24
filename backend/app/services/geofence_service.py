import asyncio
import requests
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from sqlalchemy import select
from app.config import get_settings
from app.models.geofence import Geofence
from app.models.geofence_event import GeofenceEvent
from app.database import get_db, AsyncSessionLocal
from app.services.traccar_service import TraccarService
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GeofenceState:
    """Armazena estado atual de cada dispositivo (qual geofence está dentro)"""
    _state: Dict[int, Optional[str]] = {}  # device_id -> geofence_id

    @classmethod
    def get(cls, device_id: int) -> Optional[str]:
        return cls._state.get(device_id)

    @classmethod
    def set(cls, device_id: int, geofence_id: Optional[str]):
        if geofence_id:
            cls._state[device_id] = geofence_id
        else:
            cls._state.pop(device_id, None)

async def get_db_session():
    """Obtém uma nova sessão de banco de dados assíncrona"""
    return AsyncSessionLocal()

async def check_all_devices():
    """Verifica todos os dispositivos ativos contra todas as geofences"""
    settings = get_settings()
    traccar_url = settings.traccar_url

    # 1. Buscar geofences ativas do banco backend
    db = await get_db_session()
    try:
        result = await db.execute(select(Geofence).where(Geofence.is_active == True))
        geofences = result.scalars().all()
    finally:
        await db.close()

    if not geofences:
        logger.warning("Nenhuma geofence ativa encontrada.")
        return

    # 2. Buscar dispositivos e suas últimas posições via API do Traccar
    traccar = TraccarService()
    try:
        devices = await traccar.get_all_devices()
    except Exception as e:
        logger.error(f"Erro ao buscar dispositivos do Traccar: {e}")
        return

    if not devices:
        logger.warning("Nenhum dispositivo retornado do Traccar.")
        return

    for device in devices:
        device_id = device['id']
        # Buscar última posição
        try:
            pos_response = requests.get(
                f"{traccar_url}/api/positions",
                params={"deviceId": device_id, "limit": 1, "sort": "desc"},
                cookies={"JSESSIONID": traccar.session_cookie},
                timeout=5
            )
            pos_response.raise_for_status()
            positions = pos_response.json()
            if not positions:
                continue
            last_pos = positions[0]
            lat = last_pos['latitude']
            lon = last_pos['longitude']
            point = Point(lon, lat)
        except Exception as e:
            logger.error(f"Erro ao buscar posição do dispositivo {device_id}: {e}")
            continue

        # 3. Verificar se está dentro de alguma geofence
        inside_geofence_id = None
        for gf in geofences:
            if is_point_in_geofence(point, gf):
                inside_geofence_id = gf.id
                break

        # 4. Comparar com estado anterior e gerar eventos
        previous = GeofenceState.get(device_id)
        if inside_geofence_id and inside_geofence_id != previous:
            # ENTRADA
            await save_event(device_id, inside_geofence_id, 'enter', lat, lon)
            GeofenceState.set(device_id, inside_geofence_id)
            logger.info(f"Dispositivo {device_id} entrou na geofence {inside_geofence_id}")
        elif inside_geofence_id is None and previous is not None:
            # SAÍDA
            await save_event(device_id, previous, 'exit', lat, lon)
            GeofenceState.set(device_id, None)
            logger.info(f"Dispositivo {device_id} saiu da geofence {previous}")

def is_point_in_geofence(point: Point, geofence: Geofence) -> bool:
    """Verifica se um ponto está dentro de uma geofence (círculo, polígono ou retângulo)"""
    if geofence.geofence_type == "circle":
        center = Point(float(geofence.center_longitude), float(geofence.center_latitude))
        radius = geofence.radius  # metros
        return point.distance(center) <= radius
    elif geofence.geofence_type in ["polygon", "rectangle"]:
        coords = geofence.geometry.get('coordinates', [])
        if not coords:
            return False
        # Formato GeoJSON: {'type': 'Polygon', 'coordinates': [[[lon, lat], ...]]}
        if geofence.geometry.get('type') == 'Polygon':
            polygon_coords = geofence.geometry['coordinates'][0]
            poly = Polygon(polygon_coords)
            return poly.contains(point)
        else:
            # fallback para array simples
            poly = Polygon(coords)
            return poly.contains(point)
    else:
        logger.warning(f"Tipo de geofence não suportado: {geofence.geofence_type}")
        return False

async def save_event(device_id: int, geofence_id: str, event_type: str, lat: float, lon: float):
    """Salva um evento no banco"""
    db = await get_db_session()
    try:
        event = GeofenceEvent(
            device_id=device_id,
            geofence_id=geofence_id,
            event_type=event_type,
            latitude=lat,
            longitude=lon,
            timestamp=datetime.utcnow()
        )
        db.add(event)
        await db.commit()
    finally:
        await db.close()

async def start_periodic_check(interval_seconds=60):
    """Inicia a verificação periódica em background"""
    logger.info(f"Iniciando verificação periódica de geofences a cada {interval_seconds}s")
    while True:
        await check_all_devices()
        await asyncio.sleep(interval_seconds)