# path: backend/app/models/driver.py
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Enum as SAEnum, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

# IMPORTANT: models only. No FastAPI, no engine here.
from app.models.base import Base


# --- Placement audit (where a skip sits on site) -----------------------------
class SkipPlacement(Base):
    __tablename__ = "skip_placements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skip_id: Mapped[str] = mapped_column(ForeignKey("skips.id", ondelete="CASCADE"), index=True)
    zone_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    placed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    removed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# --- Enums used by movements/weights/transfers -------------------------------
class MovementType(str, Enum):
    DELIVERY_EMPTY = "DELIVERY_EMPTY"
    RELOCATION_EMPTY = "RELOCATION_EMPTY"
    COLLECTION_FULL = "COLLECTION_FULL"
    RETURN_EMPTY = "RETURN_EMPTY"


class WeightSource(str, Enum):
    LOAD_CELL = "LOAD_CELL"
    WEIGHBRIDGE = "WEIGHBRIDGE"
    ESTIMATE = "ESTIMATE"


class DestinationType(str, Enum):
    RECYCLING = "RECYCLING"
    LANDFILL = "LANDFILL"
    SORTATION = "SORTATION"
    TRANSFER_STATION = "TRANSFER_STATION"
    HAZARDOUS = "HAZARDOUS"


# --- Movement (driver actions) -----------------------------------------------
class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skip_id: Mapped[str] = mapped_column(ForeignKey("skips.id", ondelete="CASCADE"), index=True)
    type: Mapped[MovementType] = mapped_column(SAEnum(MovementType), nullable=False)
    from_zone_id: Mapped[Optional[str]] = mapped_column(String(36))
    to_zone_id: Mapped[Optional[str]] = mapped_column(String(36))
    when: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    driver_name: Mapped[Optional[str]] = mapped_column(String(120))
    vehicle_reg: Mapped[Optional[str]] = mapped_column(String(64))
    note: Mapped[Optional[str]] = mapped_column(String(300))

    weight: Mapped[Optional["Weight"]] = relationship(back_populates="movement", uselist=False, cascade="all, delete-orphan")
    transfer: Mapped[Optional["Transfer"]] = relationship(back_populates="movement", uselist=False, cascade="all, delete-orphan")


# --- Weight (one per movement) -----------------------------------------------
class Weight(Base):
    __tablename__ = "weights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    movement_id: Mapped[str] = mapped_column(ForeignKey("movements.id", ondelete="CASCADE"), unique=True)
    source: Mapped[WeightSource] = mapped_column(SAEnum(WeightSource), nullable=False)
    gross_kg: Mapped[Optional[float]] = mapped_column(Float)
    tare_kg: Mapped[Optional[float]] = mapped_column(Float)
    net_kg: Mapped[Optional[float]] = mapped_column(Float)
    at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    movement: Mapped[Movement] = relationship(back_populates="weight")


# --- Transfer (where the skip went) ------------------------------------------
class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    movement_id: Mapped[str] = mapped_column(ForeignKey("movements.id", ondelete="CASCADE"), unique=True)
    destination_type: Mapped[DestinationType] = mapped_column(SAEnum(DestinationType), nullable=False)
    destination_name: Mapped[Optional[str]] = mapped_column(String(200))
    destination_address: Mapped[Optional[str]] = mapped_column(String(300))
    site_id: Mapped[Optional[str]] = mapped_column(String(36))
    commodity_id: Mapped[Optional[str]] = mapped_column(String(36))
    transfer_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    movement: Mapped[Movement] = relationship(back_populates="transfer")


# --- Waste Transfer Note ------------------------------------------------------
class WasteTransferNote(Base):
    __tablename__ = "wtns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transfer_id: Mapped[str] = mapped_column(ForeignKey("transfers.id", ondelete="CASCADE"), unique=True)
    description: Mapped[str] = mapped_column(String(300))
    ewc_code: Mapped[Optional[str]] = mapped_column(String(20))
    quantity_kg: Mapped[Optional[float]] = mapped_column(Float)
    producer_name: Mapped[Optional[str]] = mapped_column(String(120))
    carrier_name: Mapped[Optional[str]] = mapped_column(String(120))
    destination_name: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

# --- Driver Profile (compat with existing app.api.drivers) ---
class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(40))
    license_no: Mapped[Optional[str]] = mapped_column(String(40))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

DBPlacement = SkipPlacement

__all__ = [
    "SkipPlacement",
    "DBPlacement",
    "MovementType",
    "WeightSource",
    "DestinationType",
    "Movement",
    "Weight",
    "Transfer",
    "WasteTransferNote",
    "DriverProfile",
    "Base",
]
