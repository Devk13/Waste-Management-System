# path: backend/app/api/dev.py
from __future__ import annotations

from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Body, Query, HTTPException, status, Header
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.deps import get_db
from app.models.skip import Skip  # single source of truth
from app.models import models as m  # used in seed only

router = APIRouter(tags=["dev"])


# ---------- Models ----------
class EnsureSkipIn(BaseModel):
    qr: Optional[str] = Field(default=None, description="QR code/string for the skip")
    driver_name: Optional[str] = None
    vehicle_reg: Optional[str] = None
    zone_id: Optional[str] = None
    site_id: Optional[str] = None


class EnsureSkipOut(BaseModel):
    id: str
    qr: str
    status: Optional[str] = None


class SkipCreate(BaseModel):
    owner_org_id: str
    qr_code: str
    size: str | None = None
    color: str | None = None


# ---------- Endpoints ----------
@router.api_route(
    "/ensure-skip",
    methods=["GET", "POST"],  # tolerate both for dev UX
    response_model=EnsureSkipOut,
)
async def ensure_skip(
    qr: Optional[str] = Query(None),
    payload: EnsureSkipIn | Dict[str, Any] | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
) -> EnsureSkipOut:
    """
    Dev-only helper: ensure a Skip exists for a given `qr`.
    - Accepts GET/POST, with `qr` in query or JSON body.
    - If missing, autogenerates a predictable value to prevent 422/400s in MVP.
    """
    body_qr: Optional[str] = None
    if isinstance(payload, dict):
        body_qr = payload.get("qr")
    elif isinstance(payload, EnsureSkipIn):
        body_qr = payload.qr

    qr_val = (qr or body_qr or "QRDEV-001").strip()

    # Upsert minimal skip
    res = await db.execute(select(Skip).where(Skip.qr_code == qr_val))
    skip = res.scalar_one_or_none()
    if not skip:
        skip = Skip(qr_code=qr_val, status="available")  # why: lets driver flow proceed
        db.add(skip)
        await db.commit()
        await db.refresh(skip)

    return EnsureSkipOut(id=str(skip.id), qr=skip.qr_code, status=getattr(skip, "status", None))


@router.post("/seed/skip", response_model=Dict[str, str])
async def seed_skip(
    payload: SkipCreate,
    session: AsyncSession = Depends(get_db),
    x_dev_secret: str | None = Header(default=None, alias="X-Dev-Secret"),
):
    """
    Seed a full Skip row. Guarded by a header secret.
    """
    # Why: prevents accidental seeding in prod; reuse existing secret.
    if x_dev_secret != getattr(settings, "JWT_SECRET", None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Conflict if QR exists
    existing = await session.execute(select(m.Skip).where(m.Skip.qr_code == payload.qr_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="qr_code already exists")

    skip = m.Skip(
        owner_org_id=payload.owner_org_id,
        qr_code=payload.qr_code,
        size=payload.size,
        color=payload.color,
    )
    session.add(skip)
    await session.flush()  # why: ensure id populated before commit
    await session.commit()
    return {"id": str(skip.id), "qr_code": skip.qr_code}
