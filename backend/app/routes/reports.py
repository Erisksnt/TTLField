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
from app.models.geofence_event import GeofenceEvent
from app.models.alert import Alert
from app.schemas.report import (
    ReportSummary,
    RoutePoint,
    GeofenceEventReport,
    StopPoint,
    ReportAlert,
)
from app.services.tracking_service import TrackingService
from app.services.traccar_service import TraccarService
from app.services.report_service import ReportService
import logging

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)


@router.get("/health/traccar")
async def check_traccar_health():
    """
    Verifica conexão com o servidor Traccar.
    Retorna status da conexão e lista de dispositivos disponíveis.
    """
    try:
        traccar = TraccarService()
        
        # Tentar obter devices do Traccar
        from datetime import timedelta
        now = datetime.now()
        start_dt = now - timedelta(hours=1)
        end_dt = now
        
        logger.info("Testando conexão com Traccar...")
        
        # Fazer request direto à API do Traccar
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
                "devices": [
                    {
                        "id": d.get("id"),
                        "name": d.get("name"),
                        "uniqueId": d.get("uniqueId"),
                        "category": d.get("category")
                    }
                    for d in devices
                ],
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"❌ Erro ao conectar com Traccar: Status {response.status_code}")
            return {
                "status": "❌ Erro de conexão",
                "traccar_url": traccar.base_url,
                "error": f"HTTP {response.status_code}",
                "response": response.text[:500] if response.text else "Sem resposta",
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        logger.error(f"❌ Erro ao testar Traccar: {str(e)}")
        return {
            "status": "❌ Erro de conexão",
            "error": str(e),
            "message": "Verifique se o Traccar está rodando e acessível no IP configurado",
            "timestamp": datetime.now().isoformat()
        }


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

    metrics = ReportService.calculate_report_metrics(positions_data)
    stops_data = ReportService.identify_stops(positions_data)
    
    logger.info(
        f"Relatório com {metrics['journeys_count']} viagens: "
        f"distância={metrics['total_distance_km']}km, "
        f"tempo={metrics['total_time_minutes']}min, "
        f"velocidade_média={metrics['average_speed_kmh']}km/h"
    )

    # Buscar eventos e alertas
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
    for enriched in ReportService.enrich_route_points(positions_data):
        pos = enriched["position"]
        try:
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


@router.get("/geofence-events/{technician_id}", response_model=List[GeofenceEventReport])
async def get_geofence_events(
    technician_id: str,
    start_date: str = Query(..., description="Data inicial (ISO 8601)"),
    end_date: str = Query(..., description="Data final (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtém os eventos de geofence de um técnico em um período.
    Consulta a tabela geofence_events (inserida pelo serviço de geofence).
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
            timestamp=event.timestamp,
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
    Usa a nova lógica melhorada que filtra ruído GPS e períodos de inatividade longa.
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)")

    # Buscar técnico para obter device_id
    stmt = select(Technician).where(Technician.id == technician_id)
    result = await db.execute(stmt)
    technician = result.scalar_one_or_none()
    if not technician or not technician.device_id:
        logger.warning(f"Técnico {technician_id} sem device_id")
        return []

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

    # Serviço para identificar paradas
    stops_data = ReportService.identify_stops(positions_data, min_stop_duration_minutes=2)
    
    stops = [
        StopPoint(
            latitude=stop["latitude"],
            longitude=stop["longitude"],
            start_time=stop["start_time"],
            end_time=stop["end_time"],
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
