# path: backend/app/models/skip.py
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base  # ← use the shared Base

if TYPE_CHECKING:
    from .labels import SkipAsset  # only for type hints


class SkipStatus(str, Enum):
    IN_STOCK = "in_stock"
    DEPLOYED = "deployed"
    IN_TRANSIT = "in_transit"
    PROCESSING = "processing"


class Skip(Base):
    __tablename__ = "skips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    qr_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    owner_org_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    assigned_commodity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    zone_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default=SkipStatus.IN_STOCK.value, nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    created_by_id: Mapped[str | None] = mapped_column(String(36), default=None)
    updated_by_id: Mapped[str | None] = mapped_column(String(36), default=None)

    assets: Mapped[list["SkipAsset"]] = relationship(
        "SkipAsset", back_populates="skip", cascade="all, delete-orphan"
    )
