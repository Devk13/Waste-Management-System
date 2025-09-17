from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base

def _uuid():
    return str(uuid.uuid4())

class SkipAssignment(Base):
    __tablename__ = "skip_assignments"
    id = Column(String, primary_key=True, default=_uuid)
    skip_id = Column(String, ForeignKey("skips.id", ondelete="CASCADE"), nullable=False)
    contractor_id = Column(String, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now(), nullable=False)
    unassigned_at = Column(DateTime, nullable=True)
    __table_args__ = (
        # Prevent a skip from having two active owners at once
        UniqueConstraint("skip_id", "unassigned_at", name="uq_skip_active_assignment"),
    )

