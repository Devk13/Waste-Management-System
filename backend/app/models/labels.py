# path: backend/app/models/labels.py
from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base

Base = declarative_base()  # local Base for label assets

if TYPE_CHECKING:
    from .skip import Skip  # only for type hints


class SkipAssetKind:
    label_png = "label_png"
    labels_pdf = "labels_pdf"


class SkipAsset(Base):
    __tablename__ = "skip_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    skip_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    idx: Mapped[int | None] = mapped_column(default=None)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)

    # 👇 rename Python attribute to 'data', keep column name "bytes"
    data: Mapped[bytes] = mapped_column("bytes", nullable=False)

    # relationships
    skip: Mapped["Skip"] = relationship("Skip", back_populates="assets")
