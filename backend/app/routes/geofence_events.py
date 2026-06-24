from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models.geofence_event import GeofenceEvent
from app.models.device import Device

router = APIRouter(
    prefix="/geofence-events",
    tags=["Geofence Events"]
)

@router.get("/")
def get_geofence_events(
    device_id: Optional[int] = Query(None, description="Filtrar por ID do dispositivo (Traccar)"),
    geofence_id: Optional[str] = Query(None, description="Filtrar por ID da geofence (UUID)"),
    event_type: Optional[str] = Query(None, description="Filtrar por tipo: 'enter' ou 'exit'"),
    from_date: Optional[datetime] = Query(None, description="Data/hora inicial (ISO 8601)"),
    to_date: Optional[datetime] = Query(None, description="Data/hora final (ISO 8601)"),
    limit: int = Query(100, ge=1, le=500, description="Limite de registros retornados"),
    offset: int = Query(0, ge=0, description="Páginação - deslocamento"),
    db: Session = Depends(get_db)
):
    """
    Retorna eventos de entrada/saída de geofences.
    """
    query = db.query(GeofenceEvent)

    if device_id:
        query = query.filter(GeofenceEvent.device_id == device_id)
    if geofence_id:
        query = query.filter(GeofenceEvent.geofence_id == geofence_id)
    if event_type:
        if event_type not in ['enter', 'exit']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="event_type deve ser 'enter' ou 'exit'"
            )
        query = query.filter(GeofenceEvent.event_type == event_type)
    if from_date:
        query = query.filter(GeofenceEvent.timestamp >= from_date)
    if to_date:
        query = query.filter(GeofenceEvent.timestamp <= to_date)

    total = query.count()
    events = query.order_by(GeofenceEvent.timestamp.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "events": events
    }


@router.get("/current-state/{device_id}")
def get_current_geofence_state(
    device_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna a última geofence em que o dispositivo está (entrada sem saída).
    Útil para saber onde o dispositivo está atualmente.
    """
    # Buscar o último evento de entrada para este dispositivo
    last_enter = db.query(GeofenceEvent)\
        .filter(GeofenceEvent.device_id == device_id, GeofenceEvent.event_type == 'enter')\
        .order_by(GeofenceEvent.timestamp.desc()).first()

    if not last_enter:
        return {"device_id": device_id, "geofence_id": None, "inside": False}

    # Verificar se há uma saída posterior a essa entrada
    last_exit = db.query(GeofenceEvent)\
        .filter(
            GeofenceEvent.device_id == device_id,
            GeofenceEvent.event_type == 'exit',
            GeofenceEvent.timestamp > last_enter.timestamp
        )\
        .order_by(GeofenceEvent.timestamp.desc()).first()

    if last_exit:
        # Sair depois da entrada -> não está mais dentro
        return {"device_id": device_id, "geofence_id": None, "inside": False}
    else:
        # Ainda está dentro da geofence da última entrada
        return {
            "device_id": device_id,
            "geofence_id": last_enter.geofence_id,
            "inside": True,
            "since": last_enter.timestamp
        }