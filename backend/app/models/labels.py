# path: backend/app/models/labels.py
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SkipAssetKind:
    label_png = "label_png"     # single PNG (idx 1..3)
    labels_pdf = "labels_pdf"   # 3-up PDF sheet


class SkipAsset(Base):
    __tablename__ = "skip_assets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    skip_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skips.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    idx: Mapped[int | None] = mapped_column(default=None)  # 1..3 for PNG; None for PDF
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    # why: enable Skip.assets backref + cascade cleanup
    skip = relationship("Skip", back_populates="assets")
