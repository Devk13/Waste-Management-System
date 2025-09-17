# ======================================================================
# file: backend/app/models/driver_schedule.py
# ======================================================================
from __future__ import annotations
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from app.models.base import Base

def _uuid() -> str: return str(uuid.uuid4())

class DriverTask(Base):
    __tablename__ = "driver_tasks"
    id = Column(String, primary_key=True, default=_uuid)
    driver_name = Column(String, index=True, nullable=False)
    task_type = Column(String, nullable=False)              # deliver-empty | relocate-empty | collect-full | return-empty | note
    skip_qr = Column(String, nullable=True, index=True)
    to_zone_id = Column(String, nullable=True)
    destination_name = Column(String, nullable=True)
    destination_type = Column(String, nullable=True)
    gross_kg = Column(Float, nullable=True)
    tare_kg = Column(Float, nullable=True)
    scheduled_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    done = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
