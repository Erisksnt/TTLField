import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Set

import httpx
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.geofence import Geofence
from app.models.geofence_event import GeofenceEvent
from app.services.traccar_service import TraccarService
from app.services.tracking_service import TrackingService

logger = logging.getLogger(__name__)


class GeofenceState:
    """Current known geofences per Traccar device."""
    _state: Dict[int, Set[str]] = {}

    @classmethod
    def get(cls, device_id: int) -> Optional[Set[str]]:
        state = cls._state.get(device_id)
        return set(state) if state is not None else None

    @classmethod
    def set(cls, device_id: int, geofence_ids: Set[str]):
        cls._state[device_id] = set(geofence_ids)


async def get_db_session():
    return AsyncSessionLocal()


async def check_all_devices():
    settings = get_settings()
    traccar = TraccarService()

    db = await get_db_session()
    try:
        result = await db.execute(select(Geofence).where(Geofence.is_active == True))
        geofences = result.scalars().all()
    finally:
        await db.close()

    if not geofences:
        logger.warning("Nenhuma geofence ativa encontrada.")
        return

    try:
        devices = await traccar.get_all_devices()
    except Exception as exc:
        logger.error("Erro ao buscar dispositivos do Traccar: %s", exc)
        return

    if not devices:
        logger.warning("Nenhum dispositivo retornado do Traccar.")
        return

    async with httpx.AsyncClient(timeout=5) as client:
        for device in devices:
            device_id = device["id"]

            try:
                response = await client.get(
                    f"{settings.traccar_url}/api/positions",
                    params={"deviceId": device_id, "limit": 1, "sort": "desc"},
                    cookies={"JSESSIONID": traccar.session_cookie},
                )
                response.raise_for_status()
                positions = response.json()
            except Exception as exc:
                logger.error("Erro ao buscar posicao do dispositivo %s: %s", device_id, exc)
                continue

            if not positions:
                continue

            last_pos = positions[0]
            lat = last_pos.get("latitude")
            lon = last_pos.get("longitude")
            if lat is None or lon is None:
                continue

            point = Point(lon, lat)
            event_time = parse_traccar_time(last_pos.get("fixTime") or last_pos.get("serverTime"))
            inside_geofence_ids = {
                geofence.id
                for geofence in geofences
                if is_point_in_geofence(point, geofence)
            }

            previous_geofence_ids = GeofenceState.get(device_id)
            if previous_geofence_ids is None:
                previous_geofence_ids = await load_device_state(device_id)

            entered = inside_geofence_ids - previous_geofence_ids
            exited = previous_geofence_ids - inside_geofence_ids
            geofences_by_id = {geofence.id: geofence for geofence in geofences}

            for geofence_id in exited:
                geofence = geofences_by_id.get(geofence_id)
                if not geofence or geofence.alert_on_exit:
                    await save_event(device_id, geofence_id, "exit", lat, lon, event_time)
                    logger.info("Dispositivo %s saiu da geofence %s", device_id, geofence_id)

            for geofence_id in entered:
                geofence = geofences_by_id.get(geofence_id)
                if not geofence or geofence.alert_on_enter:
                    await save_event(device_id, geofence_id, "enter", lat, lon, event_time)
                    logger.info("Dispositivo %s entrou na geofence %s", device_id, geofence_id)

            GeofenceState.set(device_id, inside_geofence_ids)


async def load_device_state(device_id: int) -> Set[str]:
    db = await get_db_session()
    try:
        result = await db.execute(
            select(GeofenceEvent).where(GeofenceEvent.device_id == device_id).order_by(GeofenceEvent.timestamp)
        )
        events = result.scalars().all()
    finally:
        await db.close()

    state: Set[str] = set()
    for event in events:
        if event.event_type == "enter":
            state.add(event.geofence_id)
        elif event.event_type == "exit":
            state.discard(event.geofence_id)

    GeofenceState.set(device_id, state)
    return state


def is_point_in_geofence(point: Point, geofence: Geofence) -> bool:
    if geofence.geofence_type == "circle":
        if geofence.center_latitude is None or geofence.center_longitude is None or geofence.radius is None:
            return False

        distance_m = TrackingService.haversine(
            float(geofence.center_longitude),
            float(geofence.center_latitude),
            point.x,
            point.y,
        )
        return distance_m <= float(geofence.radius)

    if geofence.geofence_type in ["polygon", "rectangle"]:
        coords = geofence.geometry.get("coordinates", []) if geofence.geometry else []
        if not coords:
            return False

        polygon_coords = coords[0] if geofence.geometry.get("type") == "Polygon" else coords
        polygon = Polygon(polygon_coords)
        return polygon.contains(point) or polygon.touches(point)

    logger.warning("Tipo de geofence nao suportado: %s", geofence.geofence_type)
    return False


async def save_event(
    device_id: int,
    geofence_id: str,
    event_type: str,
    lat: float,
    lon: float,
    timestamp: Optional[datetime] = None,
):
    db = await get_db_session()
    try:
        event = GeofenceEvent(
            device_id=device_id,
            geofence_id=geofence_id,
            event_type=event_type,
            latitude=lat,
            longitude=lon,
            timestamp=timestamp or datetime.utcnow(),
        )
        db.add(event)
        await db.commit()
    finally:
        await db.close()


def parse_traccar_time(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None


async def start_periodic_check(interval_seconds=60):
    logger.info("Iniciando verificacao periodica de geofences a cada %ss", interval_seconds)
    while True:
        await check_all_devices()
        await asyncio.sleep(interval_seconds)
