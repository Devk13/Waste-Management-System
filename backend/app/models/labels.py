# path: backend/app/models/labels.py
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

Base = declarative_base()  # <-- local Base for label assets

if TYPE_CHECKING:
    from .skip import Skip  # only for type hints


class SkipAssetKind:
    label_png = "label_png"
    labels_pdf = "labels_pdf"


class SkipAsset(Base):
    __tablename__ = "skip_assets"

    # PK generated automatically (your API doesn't pass one)
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # IMPORTANT: tie to skips.id so the relationship works
    skip_id: Mapped[str] = mapped_column(
        ForeignKey("skips.id"), index=True, nullable=False
    )

    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    idx: Mapped[int | None] = mapped_column(default=None)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    bytes: Mapped[bytes] = mapped_column(nullable=False)

    # backref to Skip
    skip: Mapped["Skip"] = relationship("Skip", back_populates="assets")
