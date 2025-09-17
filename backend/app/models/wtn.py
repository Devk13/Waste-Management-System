from __future__ import annotations
import uuid
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

def _uuid() -> str:
    return str(uuid.uuid4())

class WasteTransferNote(Base):
    __tablename__ = "waste_transfer_notes"
    id = Column(String, primary_key=True, default=_uuid)
    number = Column(String, nullable=True, index=True)   # optional human-friendly number
    payload_json = Column(Text, nullable=False)          # why: keep render context portable
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

