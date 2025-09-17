from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from app.models.base import Base

def _uuid():
    return str(uuid.uuid4())

class Contractor(Base):
    __tablename__ = "contractors"
    id = Column(String, primary_key=True, default=_uuid)  # works on SQLite & Postgres
    org_name = Column(String, nullable=False, index=True)
    contact_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    billing_address = Column(String, nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())

