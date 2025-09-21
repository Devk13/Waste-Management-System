# path: backend/app/models/job.py

from __future__ import annotations
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, String, Text, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column, declarative_base

# Why: keep model self-contained; we create its table with checkfirst at runtime.
Base = declarative_base()

class JobType(str, enum.Enum):
    DELIVER_EMPTY = "DELIVER_EMPTY"
    RELOCATE_EMPTY = "RELOCATE_EMPTY"
    COLLECT_FULL = "COLLECT_FULL"
    RETURN_EMPTY = "RETURN_EMPTY"

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False)

    skip_qr: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    from_zone_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    to_zone_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    site_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    destination_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    destination_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    window_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    window_end:   Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    assigned_driver_id:  Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    assigned_vehicle_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_driver_status", "assigned_driver_id", "status"),
        Index("ix_jobs_window", "window_start", "window_end"),
    )
