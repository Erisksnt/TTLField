## backend/app/schemas/report.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ReportSummary(BaseModel):
    """Resumo das estatísticas do relatório"""
    total_distance_km: float
    total_time_minutes: float
    average_speed_kmh: float
    max_speed_kmh: float
    total_stops: int
    geofence_events_count: int
    alerts_count: int


class RoutePoint(BaseModel):
    """Ponto da rota"""
    latitude: float
    longitude: float
    timestamp: datetime
    speed: Optional[float] = None


class GeofenceEventReport(BaseModel):
    """Evento de geofence para relatório"""
    geofence_name: str
    event_type: str  # "enter" ou "exit"
    timestamp: datetime
    latitude: float
    longitude: float


class StopPoint(BaseModel):
    """Ponto de parada"""
    latitude: float
    longitude: float
    start_time: datetime
    end_time: datetime
    duration_minutes: float


class ReportAlert(BaseModel):
    """Alerta para relatório"""
    id: str
    alert_type: str
    description: Optional[str]
    severity: str
    triggered_at: datetime
    is_acknowledged: bool