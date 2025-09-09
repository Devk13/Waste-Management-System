# path: backend/app/schemas/skip.py
from __future__ import annotations

import uuid
from typing import Optional
from pydantic import BaseModel, Field


class SkipCreate(BaseModel):
    owner_org_id: uuid.UUID
    qr_code: Optional[str] = Field(None, max_length=64)
    assigned_commodity_id: Optional[uuid.UUID] = None
    zone_id: Optional[uuid.UUID] = None


class SkipOut(BaseModel):
    id: uuid.UUID
    qr_code: str
    owner_org_id: uuid.UUID
    labels_pdf_url: str
    label_png_urls: list[str]
