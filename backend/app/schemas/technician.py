from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class TechnicianBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    employee_id: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    notes: Optional[str] = None


class TechnicianCreate(TechnicianBase):
    pass


class TechnicianUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class TechnicianLocationResponse(BaseModel):
    id: str
    name: str
    employee_id: str
    is_online: bool
    latitude: Optional[float]
    longitude: Optional[float]
    accuracy: Optional[float]
    battery_level: Optional[int]
    last_seen: Optional[datetime]
    device_id: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class TechnicianResponse(TechnicianBase):
    id: str
    is_active: bool
    is_online: bool
    latitude: Optional[float]
    longitude: Optional[float]
    accuracy: Optional[float]
    battery_level: Optional[int]
    device_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_seen: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class TechnicianDetailResponse(TechnicianResponse):
    device_id: Optional[str]
