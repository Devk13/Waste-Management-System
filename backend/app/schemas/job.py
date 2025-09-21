# path: backend/app/schemas/job.py

from __future__ import annotations
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict  # pydantic v2

JobType = Literal["DELIVER_EMPTY", "RELOCATE_EMPTY", "COLLECT_FULL", "RETURN_EMPTY"]
JobStatus = Literal["PENDING", "IN_PROGRESS", "DONE", "FAILED"]
DestinationType = Literal["RECYCLING", "LANDFILL", "TRANSFER"]

class JobBase(BaseModel):
    type: JobType
    skip_qr: Optional[str] = None
    from_zone_id: Optional[str] = None
    to_zone_id: Optional[str] = None
    site_id: Optional[str] = None
    destination_type: Optional[DestinationType] = None
    destination_name: Optional[str] = None
    window_start: Optional[datetime] = Field(None, description="ISO8601")
    window_end:   Optional[datetime] = Field(None, description="ISO8601")
    assigned_driver_id: Optional[str] = None
    assigned_vehicle_id: Optional[str] = None
    notes: Optional[str] = None

    # Pydantic v2
    model_config = {"from_attributes": True}

class JobCreate(JobBase):
    status: Optional[JobStatus] = "PENDING"

class JobUpdate(BaseModel):
    type: Optional[JobType] = None
    skip_qr: Optional[str] = None
    from_zone_id: Optional[str] = None
    to_zone_id: Optional[str] = None
    site_id: Optional[str] = None
    destination_type: Optional[DestinationType] = None
    destination_name: Optional[str] = None
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    assigned_driver_id: Optional[str] = None
    assigned_vehicle_id: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[JobStatus] = None

    model_config = {"from_attributes": True}

# Compat alias so routers can `from app.schemas.job import JobPatch`
class JobPatch(JobUpdate):
    pass

class JobOut(JobBase):
    id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
