from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy.orm import declarative_base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# app/models/skip.py  (same idea for labels.py, driver.py, etc.)

# This module's own Base so we can bootstrap it independently
Base = declarative_base()

if TYPE_CHECKING:  # only for type checkers; avoids import cycles at runtime
    from .labels import SkipAsset


class SkipStatus(str, Enum):
    IN_STOCK = "in_stock"
    DEPLOYED = "deployed"
    IN_TRANSIT = "in_transit"
    PROCESSING = "processing"


class Skip(Base):
    __tablename__ = "skips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    qr_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    owner_org_id: Mapped[str] = mapped_column(String(36), nullable=False)
    assigned_commodity_id: Mapped[str | None] = mapped_column(String(36), default=None)
    zone_id: Mapped[str | None] = mapped_column(String(36), default=None)

    status: Mapped[str] = mapped_column(String(32), default=SkipStatus.IN_STOCK.value, nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    created_by_id: Mapped[str | None] = mapped_column(String(36), default=None)
    updated_by_id: Mapped[str | None] = mapped_column(String(36), default=None)

    assets: Mapped[list["SkipAsset"]] = relationship(
        "SkipAsset", back_populates="skip", cascade="all,delete-orphan"
    )
