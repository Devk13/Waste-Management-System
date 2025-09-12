# path: backend/app/api/dev.py
from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db import get_session
from app.models import models as m

router = APIRouter(prefix="/__dev", tags=["__dev"])

class SkipCreate(BaseModel):
    owner_org_id: str
    qr_code: str
    size: str | None = None
    color: str | None = None

@router.post("/seed/skip")
async def seed_skip(
    payload: SkipCreate,
    session: AsyncSession = Depends(get_session),
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
