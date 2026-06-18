## backend/app/routes/reports.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.technician import Technician
from app.models.position import Position
from app.models.geofence import Geofence
from app.models.alert import Alert
from app.models.event import Event
from app.schemas.report import (
    ReportSummary,
    RoutePoint,
    GeofenceEventReport,
    StopPoint,
    ReportAlert,
)
from app.services.tracking_service import TrackingService
from app.services.traccar_service import TraccarService
import logging

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)


@router.get("/summary/{technician_id}", response_model=ReportSummary)
async def get_report_summary(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtém o resumo das estatísticas de um técnico em um período, buscando do Traccar.
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)")

    # Busca técnico para obter device_id
    stmt = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(stmt)
    technician = result.scalar_one_or_none()
    if not technician or not technician.device_id:
        logger.warning(f"Técnico {technician_id} sem device_id")
        return ReportSummary(
            total_distance_km=0.0,
            total_time_minutes=0.0,
            average_speed_kmh=0.0,
            max_speed_kmh=0.0,
            total_stops=0,
            geofence_events_count=0,
            alerts_count=0,
        )

    # Busca posições do Traccar
    traccar = TraccarService()
    positions_data = await traccar.get_device_positions(
        int(technician.device_id),
        start_dt,
        end_dt
    )

    if not positions_data or len(positions_data) < 2:
        logger.info(f"Nenhuma posição encontrada para {technician_id} no período")
        return ReportSummary(
            total_distance_km=0.0,
            total_time_minutes=0.0,
            average_speed_kmh=0.0,
            max_speed_kmh=0.0,
            total_stops=0,
            geofence_events_count=0,
            alerts_count=0,
        )

    # Ordenar por fixTime (timestamp)
    positions_data.sort(key=lambda p: p.get("fixTime", ""))

    total_distance = 0.0
    total_time_seconds = 0.0
    max_speed = 0.0
    stops = 0

    logger.info(f"📊 Calculando métricas para {len(positions_data)} pontos")

    for i in range(1, len(positions_data)):
        prev = positions_data[i-1]
        curr = positions_data[i]

        # Extrair timestamps
        prev_time_str = prev.get("fixTime") or prev.get("serverTime")
        curr_time_str = curr.get("fixTime") or curr.get("serverTime")
        if not prev_time_str or not curr_time_str:
            continue

        prev_dt = datetime.fromisoformat(prev_time_str.replace('Z', '+00:00')).replace(tzinfo=None)
        curr_dt = datetime.fromisoformat(curr_time_str.replace('Z', '+00:00')).replace(tzinfo=None)

        # Coordenadas
        lat1 = prev.get("latitude")
        lon1 = prev.get("longitude")
        lat2 = curr.get("latitude")
        lon2 = curr.get("longitude")

        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            continue

        # 🔥 Cálculo de distância usando função haversine
        dist_km = TrackingService.haversine(lon1, lat1, lon2, lat2) / 1000.0
        total_distance += dist_km

        # Tempo
        time_diff = (curr_dt - prev_dt).total_seconds()
        total_time_seconds += time_diff

        # Velocidade (se disponível)
        if curr.get("speed") is not None:
            speed_kmh = curr["speed"] * 3.6
            if speed_kmh > max_speed:
                max_speed = speed_kmh

        # Parada (mais de 2 minutos e menos de 10m)
        if time_diff > 120 and dist_km < 0.01:
            stops += 1

    avg_speed = (total_distance / (total_time_seconds / 3600)) if total_time_seconds > 0 else 0.0

    logger.info(f"📊 Resultados: distância={total_distance:.2f}km, tempo={total_time_seconds:.0f}s, paradas={stops}")

    # Buscar eventos e alertas (do banco local – opcional)
    stmt_events = select(Event).where(
        and_(
            Event.technician_id == technician_id,
            Event.event_timestamp >= start_dt,
            Event.event_timestamp <= end_dt,
            Event.event_type.in_(["geofence_enter", "geofence_exit"])
        )
    )
    result_events = await db.execute(stmt_events)
    geofence_events = result_events.scalars().all()

    stmt_alerts = select(Alert).where(
        and_(
            Alert.technician_id == technician_id,
            Alert.triggered_at >= start_dt,
            Alert.triggered_at <= end_dt,
        )
    )
    result_alerts = await db.execute(stmt_alerts)
    alerts = result_alerts.scalars().all()

    return ReportSummary(
        total_distance_km=round(total_distance, 2),
        total_time_minutes=round(total_time_seconds / 60, 1),
        average_speed_kmh=round(avg_speed, 1),
        max_speed_kmh=round(max_speed, 1),
        total_stops=stops,
        geofence_events_count=len(geofence_events),
        alerts_count=len(alerts),
    )


@router.get("/route/{technician_id}", response_model=List[RoutePoint])
async def get_route(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtém os pontos da rota de um técnico em um período, consultando o Traccar.
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    # Buscar técnico para obter device_id
    stmt = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(stmt)
    technician = result.scalar_one_or_none()
    if not technician or not technician.device_id:
        raise HTTPException(status_code=404, detail="Técnico ou device_id não encontrado")

    # Buscar posições do Traccar
    traccar = TraccarService()
    try:
        positions_data = await traccar.get_device_positions(
            int(technician.device_id),
            start_dt,
            end_dt
        )
    except Exception as e:
        logger.error(f"Erro ao buscar posições do Traccar: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar dados do Traccar")

    if not positions_data:
        return []

    route_points = []
    for pos in positions_data:
        try:
            # Converte timestamp
            fix_time = pos.get("fixTime")
            if fix_time:
                if isinstance(fix_time, str):
                    ts = datetime.fromisoformat(fix_time.replace('Z', '+00:00')).replace(tzinfo=None)
                elif isinstance(fix_time, datetime):
                    ts = fix_time.replace(tzinfo=None)
                else:
                    continue
            else:
                continue

            route_points.append(
                RoutePoint(
                    latitude=pos.get("latitude"),
                    longitude=pos.get("longitude"),
                    timestamp=ts,
                    speed=pos.get("speed"),
                )
            )
        except Exception as e:
            logger.warning(f"Erro ao processar ponto: {e}")
            continue

    return route_points


@router.get("/geofence-events/{technician_id}", response_model=List[GeofenceEventReport])
async def get_geofence_events(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtém os eventos de geofence de um técnico em um período.
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    stmt = select(Event, Geofence).join(
        Geofence, Event.geofence_id == Geofence.id
    ).where(
        and_(
            Event.technician_id == technician_id,
            Event.event_timestamp >= start_dt,
            Event.event_timestamp <= end_dt,
            Event.event_type.in_(["geofence_enter", "geofence_exit"])
        )
    ).order_by(Event.event_timestamp)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        GeofenceEventReport(
            geofence_name=geofence.name,
            event_type=event.event_type.replace("geofence_", ""),
            timestamp=event.event_timestamp,
            latitude=event.latitude,
            longitude=event.longitude,
        )
        for event, geofence in rows
    ]


@router.get("/stops/{technician_id}", response_model=List[StopPoint])
async def get_stops(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtém os pontos de parada de um técnico em um período.
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    stmt = select(Position).where(
        and_(
            Position.technician_id == technician_id,
            Position.timestamp >= start_dt,
            Position.timestamp <= end_dt,
        )
    ).order_by(Position.timestamp)
    
    result = await db.execute(stmt)
    positions = result.scalars().all()
    
    stops = []
    i = 0
    while i < len(positions):
        if i + 1 < len(positions):
            dist = TrackingService.haversine(
                positions[i].longitude, positions[i].latitude,
                positions[i+1].longitude, positions[i+1].latitude
            )
            time_diff = (positions[i+1].timestamp - positions[i].timestamp).total_seconds()
            
            if time_diff > 120 and dist < 10:
                start_stop = positions[i]
                end_stop = positions[i]
                j = i + 1
                while j < len(positions):
                    d = TrackingService.haversine(
                        start_stop.longitude, start_stop.latitude,
                        positions[j].longitude, positions[j].latitude
                    )
                    if d > 10 or (positions[j].timestamp - start_stop.timestamp).total_seconds() > 600:
                        break
                    end_stop = positions[j]
                    j += 1
                
                duration = (end_stop.timestamp - start_stop.timestamp).total_seconds() / 60
                if duration >= 2:
                    stops.append(StopPoint(
                        latitude=start_stop.latitude,
                        longitude=start_stop.longitude,
                        start_time=start_stop.timestamp,
                        end_time=end_stop.timestamp,
                        duration_minutes=round(duration, 1),
                    ))
                i = j
            else:
                i += 1
        else:
            break
    
    return stops


@router.get("/alerts/{technician_id}", response_model=List[ReportAlert])
async def get_alerts_report(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtém os alertas de um técnico em um período.
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    stmt = select(Alert).where(
        and_(
            Alert.technician_id == technician_id,
            Alert.triggered_at >= start_dt,
            Alert.triggered_at <= end_dt,
        )
    ).order_by(Alert.triggered_at.desc())
    
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    return [
        ReportAlert(
            id=alert.id,
            alert_type=alert.alert_type,
            description=alert.description,
            severity=alert.severity,
            triggered_at=alert.triggered_at,
            is_acknowledged=alert.is_acknowledged,
        )
        for alert in alerts
    ]