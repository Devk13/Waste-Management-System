# path: backend/app/models/labels.py
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base  # ← use the shared Base

if TYPE_CHECKING:
    from .skip import Skip


class SkipAssetKind:
    label_png = "label_png"
    labels_pdf = "labels_pdf"


class SkipAsset(Base):
    __tablename__ = "skip_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    skip_id: Mapped[str] = mapped_column(ForeignKey("skips.id"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    idx: Mapped[int | None] = mapped_column(default=None)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    bytes: Mapped[bytes] = mapped_column(nullable=False)

    skip: Mapped["Skip"] = relationship("Skip", back_populates="assets")
