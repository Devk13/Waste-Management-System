# path: backend/app/models/driver.py
from __future__ import annotations
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class DriverStatus(str, enum.Enum):
    available = "available"
    busy = "busy"
    inactive = "inactive"


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # store as 36-char UUID string to keep SQLite happy
    user_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default=DriverStatus.available.value)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DriverAssignment(Base):
    __tablename__ = "driver_assignments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    driver_user_id: Mapped[str] = mapped_column(String(36), index=True)
    skip_id: Mapped[str] = mapped_column(String(36), ForeignKey("skips.id"))
    status: Mapped[str] = mapped_column(String(20), default="assigned")
    open: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
