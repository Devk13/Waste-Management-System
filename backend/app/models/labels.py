from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from sqlalchemy.orm import declarative_base
Base = declarative_base()
from app.db import Base

if TYPE_CHECKING:
    from .skip import Skip

class SkipAssetKind(str, Enum):
    label_png = "label_png"
    labels_pdf = "labels_pdf"

class SkipAsset(Base):
    __tablename__ = "skip_assets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    skip_id: Mapped[str] = mapped_column(ForeignKey("skips.id"))
    kind: Mapped[SkipAssetKind]
    idx: Mapped[int | None]
    content_type: Mapped[str]
    bytes: Mapped[bytes]

    skip: Mapped["Skip"] = relationship(back_populates="assets")
