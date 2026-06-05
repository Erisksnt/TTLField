## backend/app/schemas/geofence.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal, Any


class GeofenceBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    geofence_type: Literal["circle"]
    alert_on_enter: bool = True
    alert_on_exit: bool = True


class GeofenceCreate(GeofenceBase):
    geometry: dict[str, Any]
    radius: Optional[int] = None 
    center_latitude: Optional[str] = None
    center_longitude: Optional[str] = None 
    address: Optional[str] = None

class GeofenceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    alert_on_enter: Optional[bool] = None
    alert_on_exit: Optional[bool] = None
    is_active: Optional[bool] = None
    radius: Optional[int] = None 
    center_latitude: Optional[str] = None 
    center_longitude: Optional[str] = None
    address: Optional[str] = None 


class GeofenceResponse(GeofenceBase):
    id: str
    geometry: dict[str, Any]
    is_active: bool
    radius: Optional[int] = None
    center_latitude: Optional[str] = None
    center_longitude: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GeofenceDetailResponse(GeofenceResponse):
    pass


class GeofenceEventResponse(BaseModel):
    id: str
    geofence_id: str
    geofence_name: str
    technician_id: str
    event_type: Literal["enter", "exit"]
    latitude: float
    longitude: float
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)