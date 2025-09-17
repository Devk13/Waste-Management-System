from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class VehicleBase(BaseModel):
    reg: str = Field(..., min_length=1)
    make_model: Optional[str] = None
    capacity_kg: Optional[float] = None
    contractor_id: Optional[str] = None
    active: bool = True

class VehicleCreate(VehicleBase): pass
class VehicleUpdate(BaseModel):
    reg: Optional[str] = None
    make_model: Optional[str] = None
    capacity_kg: Optional[float] = None
    contractor_id: Optional[str] = None
    active: Optional[bool] = None

class VehicleRead(VehicleBase):
    id: str
    class Config:
        from_attributes = True

