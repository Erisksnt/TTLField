from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
import logging

from app.database import get_db
from app.models.technician import Technician
from app.models.position import Position
from app.models.geofence import Geofence
from app.models.geofence_event import GeofenceEvent
from app.models.alert import Alert
from app.schemas.report import (
    ReportSummary,
    RoutePoint,
    GeofenceEventReport,
    StopPoint,
    ReportAlert,
    RouteMatchedResponse,
)
from app.services.tracking_service import TrackingService
from app.services.traccar_service import TraccarService
from app.services.report_service import ReportService
from app.services.route_matching_service import RouteMatchingService
from app.models.user import User
from app.utils.dependencies import get_current_user

# --- Suporte a fuso horário ---
try:
    from zoneinfo import ZoneInfo
    TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")
except ImportError:
    import pytz
    TZ_BRASILIA = pytz.timezone("America/Sao_Paulo")

def to_brasilia(dt):
    """
    Converte um datetime (com ou sem fuso) para o horário de Brasília.
    Retorna um datetime naive (sem fuso) para compatibilidade com os schemas.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_br = dt.astimezone(TZ_BRASILIA)
    return dt_br.replace(tzinfo=None)

def parse_date_to_utc(date_str: str) -> datetime:
    """
    Converte uma string ISO (ex: '2026-06-24T00:00:00') para um datetime em UTC,
    assumindo que a string representa um horário de Brasília (UTC-3).
    Retorna um datetime naive (sem fuso) no UTC.
    """
    dt_naive = datetime.fromisoformat(date_str)
    # Anexar o fuso de Brasília ao datetime
    if dt_naive.tzinfo is None:
        # Compatível com ZoneInfo e pytz
        if hasattr(TZ_BRASILIA, 'localize'):
            # pytz
            dt_br = TZ_BRASILIA.localize(dt_naive)
        else:
            # ZoneInfo
            dt_br = dt_naive.replace(tzinfo=TZ_BRASILIA)
    else:
        dt_br = dt_naive.astimezone(TZ_BRASILIA)
    # Converter para UTC
    dt_utc = dt_br.astimezone(timezone.utc).replace(tzinfo=None)
    return dt_utc

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)


@router.get("/health/traccar")
async def check_traccar_health(current_user: User = Depends(get_current_user)):
    """Verifica conexão com o servidor Traccar."""
    try:
        traccar = TraccarService()
        now = datetime.now(TZ_BRASILIA).replace(tzinfo=None)
        logger.info("Testando conexão com Traccar...")
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{traccar.base_url}/api/devices",
                headers={"Accept": "application/json"}
            )
        if response.status_code == 200:
            devices = response.json()
            logger.info(f"✅ Conexão com Traccar bem-sucedida! {len(devices)} devices encontrados")
            return {
                "status": "✅ Conectado",
                "traccar_url": traccar.base_url,
                "devices_total": len(devices),
                "devices": [{"id": d.get("id"), "name": d.get("name"), "uniqueId": d.get("uniqueId"), "category": d.get("category")} for d in devices],
                "timestamp": now.isoformat()
            }
        else:
            logger.error(f"❌ Erro ao conectar com Traccar: Status {response.status_code}")
            return {
                "status": "❌ Erro de conexão",
                "traccar_url": traccar.base_url,
                "error": f"HTTP {response.status_code}",
                "response": response.text[:500] if response.text else "Sem resposta",
                "timestamp": now.isoformat()
            }
    except Exception as e:
        logger.error(f"❌ Erro ao testar Traccar: {str(e)}")
        return {
            "status": "❌ Erro de conexão",
            "error": str(e),
            "message": "Verifique se o Traccar está rodando e acessível no IP configurado",
            "timestamp": datetime.now(TZ_BRASILIA).replace(tzinfo=None).isoformat()
        }


@router.get("/summary/{technician_id}", response_model=ReportSummary)
async def get_report_summary(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtém o resumo das estatísticas de um técnico em um período."""
    try:
        start_dt = parse_date_to_utc(start_date)
        end_dt = parse_date_to_utc(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)")

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

    metrics = ReportService.calculate_report_metrics(positions_data)
    stops_data = ReportService.identify_stops(positions_data)
    logger.info(
        f"Relatório com {metrics['journeys_count']} viagens: "
        f"distância={metrics['total_distance_km']}km, "
        f"tempo={metrics['total_time_minutes']}min, "
        f"velocidade_média={metrics['average_speed_kmh']}km/h"
    )

    try:
        device_id_int = int(technician.device_id)
    except (ValueError, TypeError):
        logger.warning(f"Device ID inválido para técnico {technician_id}: {technician.device_id}")
        device_id_int = None

    stmt_events = select(GeofenceEvent).where(
        and_(
            GeofenceEvent.device_id == device_id_int,
            GeofenceEvent.timestamp >= start_dt,
            GeofenceEvent.timestamp <= end_dt,
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
        total_distance_km=metrics['total_distance_km'],
        total_time_minutes=metrics['total_time_minutes'],
        average_speed_kmh=metrics['average_speed_kmh'],
        max_speed_kmh=metrics['max_speed_kmh'],
        total_stops=len(stops_data),
        geofence_events_count=len(geofence_events),
        alerts_count=len(alerts),
    )


@router.get("/route/{technician_id}", response_model=List[RoutePoint])
async def get_route(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtém os pontos da rota de um técnico em um período."""
    try:
        start_dt = parse_date_to_utc(start_date)
        end_dt = parse_date_to_utc(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    stmt = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(stmt)
    technician = result.scalar_one_or_none()
    if not technician or not technician.device_id:
        raise HTTPException(status_code=404, detail="Técnico ou device_id não encontrado")

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
    for enriched in ReportService.enrich_route_points(positions_data):
        pos = enriched["position"]
        try:
            fix_time = pos.get("fixTime")
            if fix_time:
                if isinstance(fix_time, str):
                    dt_utc = datetime.fromisoformat(fix_time.replace('Z', '+00:00'))
                    ts = to_brasilia(dt_utc)
                elif isinstance(fix_time, datetime):
                    ts = to_brasilia(fix_time)
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
                    journey_index=enriched["journey_index"],
                    is_journey_start=enriched["is_journey_start"],
                    is_journey_end=enriched["is_journey_end"],
                    segment_distance_km=enriched["segment_distance_km"],
                    segment_time_seconds=enriched["segment_time_seconds"],
                    segment_speed_kmh=enriched["segment_speed_kmh"],
                )
            )
        except Exception as e:
            logger.warning(f"Erro ao processar ponto: {e}")
            continue

    return route_points


@router.get("/route-matched/{technician_id}", response_model=RouteMatchedResponse)
async def get_route_matched(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtém os pontos da rota e, opcionalmente, a geometria casada pelo provedor de rota."""
    try:
        start_dt = parse_date_to_utc(start_date)
        end_dt = parse_date_to_utc(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    stmt = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(stmt)
    technician = result.scalar_one_or_none()
    if not technician or not technician.device_id:
        raise HTTPException(status_code=404, detail="Técnico ou device_id não encontrado")

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
        return RouteMatchedResponse(route=[])

    route_matching = RouteMatchingService()
    route_points = []
    journeys: Dict[int, List[Dict]] = {}

    for enriched in ReportService.enrich_route_points(positions_data):
        pos = enriched["position"]
        try:
            fix_time = pos.get("fixTime")
            if fix_time:
                if isinstance(fix_time, str):
                    dt_utc = datetime.fromisoformat(fix_time.replace('Z', '+00:00'))
                    ts = to_brasilia(dt_utc)
                elif isinstance(fix_time, datetime):
                    ts = to_brasilia(fix_time)
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
                    journey_index=enriched["journey_index"],
                    is_journey_start=enriched["is_journey_start"],
                    is_journey_end=enriched["is_journey_end"],
                    segment_distance_km=enriched["segment_distance_km"],
                    segment_time_seconds=enriched["segment_time_seconds"],
                    segment_speed_kmh=enriched["segment_speed_kmh"],
                )
            )

            ji = enriched.get('journey_index') or 0
            journeys.setdefault(ji, []).append(pos)
        except Exception as e:
            logger.warning(f"Erro ao processar ponto: {e}")
            continue

    matched_routes: Dict[int, List[List[float]]] = {}
    for ji, pts in journeys.items():
        points = [
            {"latitude": p["latitude"], "longitude": p["longitude"]}
            for p in pts
            if p.get("latitude") is not None and p.get("longitude") is not None
        ]

        if len(points) < 2:
            continue

        try:
            matched = await route_matching.match_route(points)
            if matched:
                matched_routes[ji] = matched
        except Exception as e:
            logger.warning(
                "Route matching failed for technician %s journey %s: %s",
                technician_id,
                ji,
                e,
            )
            # continue silently; frontend will fallback to raw GPS

    return RouteMatchedResponse(route=route_points, matched_routes=matched_routes or None)


@router.get("/geofence-events/{technician_id}", response_model=List[GeofenceEventReport])
async def get_geofence_events(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtém os eventos de geofence de um técnico em um período."""
    try:
        start_dt = parse_date_to_utc(start_date)
        end_dt = parse_date_to_utc(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido")

    stmt = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(stmt)
    technician = result.scalar_one_or_none()
    if not technician or not technician.device_id:
        logger.warning(f"Técnico {technician_id} sem device_id")
        return []

    try:
        device_id_int = int(technician.device_id)
    except (ValueError, TypeError):
        logger.warning(f"Device ID inválido para técnico {technician_id}: {technician.device_id}")
        return []

    stmt = select(GeofenceEvent, Geofence).join(
        Geofence, GeofenceEvent.geofence_id == Geofence.id
    ).where(
        and_(
            GeofenceEvent.device_id == device_id_int,
            GeofenceEvent.timestamp >= start_dt,
            GeofenceEvent.timestamp <= end_dt,
        )
    ).order_by(GeofenceEvent.timestamp)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        GeofenceEventReport(
            geofence_name=geofence.name,
            event_type=event.event_type,
            timestamp=to_brasilia(event.timestamp),
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
    current_user: User = Depends(get_current_user),
):
    """Obtém os pontos de parada de um técnico em um período."""
    try:
        start_dt = parse_date_to_utc(start_date)
        end_dt = parse_date_to_utc(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)")

    stmt = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(stmt)
    technician = result.scalar_one_or_none()
    if not technician or not technician.device_id:
        logger.warning(f"Técnico {technician_id} sem device_id")
        return []

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

    stops_data = ReportService.identify_stops(positions_data, min_stop_duration_minutes=2)
    await ReportService.ensure_stop_addresses(stops_data)
    stops = [
        StopPoint(
            latitude=stop["latitude"],
            longitude=stop["longitude"],
            start_time=to_brasilia(stop["start_time"]),
            end_time=to_brasilia(stop["end_time"]),
            duration_minutes=stop["duration_minutes"],
            address=stop.get("address"),
        )
        for stop in stops_data
    ]
    logger.info(f"Identificadas {len(stops)} paradas para técnico {technician_id}")
    return stops


@router.get("/alerts/{technician_id}", response_model=List[ReportAlert])
async def get_alerts_report(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtém os alertas de um técnico em um período."""
    try:
        start_dt = parse_date_to_utc(start_date)
        end_dt = parse_date_to_utc(end_date)
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
            triggered_at=to_brasilia(alert.triggered_at),
            is_acknowledged=alert.is_acknowledged,
        )
        for alert in alerts
    ]