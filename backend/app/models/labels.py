# path: backend/app/models/labels.py
from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# CRUCIAL: use the shared Base so SQLAlchemy sees Skip <-> SkipAsset in the same registry
from app.models.base import Base

if TYPE_CHECKING:  # only for type hints; avoids circular imports at runtime
    from .skip import Skip


class SkipAssetKind:
    label_png = "label_png"
    labels_pdf = "labels_pdf"


class SkipAsset(Base):
    __tablename__ = "skip_assets"


    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    # IMPORTANT: FK so SQLAlchemy can join Skip <-> SkipAsset
    skip_id: Mapped[str] = mapped_column(ForeignKey("skips.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    idx: Mapped[int | None] = mapped_column(default=None)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)


    # store bytes; attribute named 'data' but column remains 'bytes'
    data: Mapped[bytes] = mapped_column("bytes", nullable=False)


    # relationships
    skip: Mapped["Skip"] = relationship("Skip", back_populates="assets")


__all__ = ["SkipAsset", "SkipAssetKind", "Base"]
