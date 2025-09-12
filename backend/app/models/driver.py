# path: backend/app/models/driver.py
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

Base = declarative_base()  # <-- local Base for driver models only

class DriverStatus(str, Enum):
    available = "available"
    busy = "busy"
    inactive = "inactive"


class DriverProfile(Base):
    __tablename__ = "driver_profiles"

    # use user_id as the PK; one profile per user
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), default=DriverStatus.available.value, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class DriverAssignment(Base):
    __tablename__ = "driver_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    driver_user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    skip_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)

    open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="assigned", nullable=False)
