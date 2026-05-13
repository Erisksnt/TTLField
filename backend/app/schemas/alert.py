from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal, Any


class AlertBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "medium"


class AlertResponse(AlertBase):
    id: str
    technician_id: str
    device_id: str
    geofence_id: Optional[str]
    alert_type: str
    is_active: bool
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    metadata: Optional[dict[str, Any]]
    triggered_at: datetime
    resolved_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AlertAcknowledge(BaseModel):
    acknowledged_by: str = Field(..., min_length=1)


class AlertFilter(BaseModel):
    technician_id: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    is_active: Optional[bool] = None
    is_acknowledged: Optional[bool] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class AlertStatistics(BaseModel):
    total_alerts: int
    active_alerts: int
    acknowledged_alerts: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
    by_technician: dict[str, int]