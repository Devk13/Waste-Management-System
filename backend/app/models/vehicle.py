from __future__ import annotations
import uuid
from sqlalchemy import Column, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

def _uuid():
    return str(uuid.uuid4())

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(String, primary_key=True, default=_uuid)
    reg = Column(String, unique=True, index=True, nullable=False)
    make_model = Column(String, nullable=True)
    capacity_kg = Column(Float, nullable=True)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="SET NULL"), nullable=True)
    active = Column(Boolean, default=True, nullable=False)

