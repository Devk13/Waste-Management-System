from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class DriverCreate(BaseModel):
    name: str = Field(..., min_length=1)

class DriverRead(BaseModel):
    id: str
    name: str
    class Config:
        from_attributes = True

