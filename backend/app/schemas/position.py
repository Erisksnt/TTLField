from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class PositionCreate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    battery_status: Optional[str] = None
    provider: str = "gps"


class PositionResponse(BaseModel):
    id: str
    technician_id: str
    device_id: str
    latitude: float
    longitude: float
    accuracy: Optional[float]
    altitude: Optional[float]
    speed: Optional[float]
    heading: Optional[float]
    battery_level: Optional[int]
    battery_status: Optional[str]
    provider: str
    is_valid: bool
    timestamp: datetime
    received_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PositionBulkCreate(BaseModel):
    positions: list[PositionCreate] = Field(..., min_items=1, max_items=100)


class PositionHistoryResponse(BaseModel):
    id: str
    latitude: float
    longitude: float
    speed: Optional[float]
    timestamp: datetime
    battery_level: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)


class RouteSegment(BaseModel):
    start_position: PositionResponse
    end_position: PositionResponse
    distance_meters: float
    duration_seconds: int
    average_speed: float