from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:  # for type checkers only
    from .skip import Skip


class SkipAssetKind(str, Enum):
    label_png = "label_png"
    labels_pdf = "labels_pdf"


class SkipAsset(Base):
    __tablename__ = "skip_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skip_id: Mapped[str] = mapped_column(String(36), ForeignKey("skips.id", ondelete="CASCADE"), index=True)

    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    idx: Mapped[int | None] = mapped_column(default=None)

    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    bytes: Mapped[bytes]

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    skip: Mapped["Skip"] = relationship("Skip", back_populates="assets")
