from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, Literal
import re

class VehicleCreate(BaseModel):
    plate: str
    owner_name: str
    roll_number: str = ""
    vehicle_type: str = ""

    @field_validator('plate')
    @classmethod
    def normalise_plate(cls, v: str) -> str:
        return re.sub(r'[^A-Z0-9]', '', v.upper())

class VehicleUpdate(BaseModel):
    plate: Optional[str] = None
    owner_name: Optional[str] = None
    roll_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    active: Optional[bool] = None

    @field_validator('plate')
    @classmethod
    def normalise_plate(cls, v: str) -> str:
        if v is None:
            return v
        return re.sub(r'[^A-Z0-9]', '', v.upper())

class VehicleOut(BaseModel):
    id: int
    plate: str
    owner_name: str
    roll_number: str
    vehicle_type: str
    active: bool
    model_config = {"from_attributes": True}

class LogOut(BaseModel):
    id: int
    plate: str
    owner_id: Optional[int]
    timestamp: datetime
    direction: Literal["IN", "OUT"]
    method: str
    confidence_score: Optional[float]
    anomaly: bool
    model_config = {"from_attributes": True}

class AlertOut(BaseModel):
    id: int
    plate: str
    timestamp: datetime
    snapshot_path: str
    resolved: bool
    model_config = {"from_attributes": True}
