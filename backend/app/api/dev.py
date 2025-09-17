# path: backend/app/api/dev.py
from __future__ import annotations
from fastapi import APIRouter, Depends, Body, Query, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.config import settings
from sqlalchemy import select
from app.api.deps import get_db
from app.models import models as m
from app.models.skip import Skip

router = APIRouter(tags=["dev"])

class SkipCreate(BaseModel):
    owner_org_id: str
    qr_code: str
    size: str | None = None
    color: str | None = None

@router.get("/ensure-skip")

@router.post("/ensure-skip")
async def ensure_skip(
    qr: Optional[str] = Query(None),
    body: Optional[dict] = Body(None),
    db: AsyncSession = Depends(get_db),
):
    # accept qr from query or body
    qr_val = qr or (body or {}).get("qr")
    if not qr_val:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="qr required")

    # upsert a bare skip with this QR
    res = await db.execute(select(Skip).where(Skip.qr_code == qr_val))
    skip = res.scalar_one_or_none()
    if not skip:
        skip = Skip(qr_code=qr_val, status="available")  # minimal fields only
        db.add(skip)
        await db.commit()
        await db.refresh(skip)

    return {"id": str(skip.id), "qr": skip.qr_code, "status": getattr(skip, "status", None)}


@router.post("/seed/skip")
async def seed_skip(
    payload: SkipCreate,
    session: AsyncSession = Depends(get_db),
    x_dev_secret: str | None = Header(default=None, alias="X-Dev-Secret"),
):
    # Guard this endpoint with a secret you control (reuse JWT_SECRET for speed)
    if x_dev_secret != settings.JWT_SECRET:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Create the skip
    skip = m.Skip(
        owner_org_id=payload.owner_org_id,
        qr_code=payload.qr_code,
        size=payload.size,
        color=payload.color,
    )
    session.add(skip)
    await session.flush()
    await session.commit()
    return {"id": str(skip.id), "qr_code": skip.qr_code}
