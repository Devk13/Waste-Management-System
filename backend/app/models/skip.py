from __future__ import annotations


import uuid
from datetime import datetime
from enum import Enum


from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.db import Base
from app.models.labels import SkipAsset




class SkipStatus(str, Enum):
IN_STOCK = "in_stock"
DEPLOYED = "deployed"
IN_TRANSIT = "in_transit"
PROCESSING = "processing"




class Skip(Base):
__tablename__ = "skips"


id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
qr_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)


owner_org_id: Mapped[uuid.UUID]
assigned_commodity_id: Mapped[uuid.UUID | None] = mapped_column(default=None)
zone_id: Mapped[uuid.UUID | None] = mapped_column(default=None)


status: Mapped[str] = mapped_column(String(32), default=SkipStatus.IN_STOCK.value, nullable=False)


created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
deleted_at: Mapped[datetime | None] = mapped_column(default=None)


created_by_id: Mapped[uuid.UUID | None] = mapped_column(default=None)
updated_by_id: Mapped[uuid.UUID | None] = mapped_column(default=None)


assets: Mapped[list[SkipAsset]] = relationship(
SkipAsset, back_populates="skip", cascade="all,delete-orphan"
)