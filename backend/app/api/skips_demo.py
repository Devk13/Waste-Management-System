# path: backend/app/api/skips_demo.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.deps import get_db # AsyncSession provider
from app.models.skip import Skip, SkipStatus

router = APIRouter(prefix="/admin/skips", tags=["admin-skips"]) # hidden behind X-Admin-Key


async def require_admin(
    x_admin_key: Optional[str] = Header(default=None, convert_underscores=False),
):
    # why: hard gate; prevents accidental exposure in prod demos
    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="bad admin key")
    
@router.post("", dependencies=[Depends(require_admin)])
async def create_skip(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Create a skip by `qr_code` (idempotent: returns existing if present)."""
    qr = (payload or {}).get("qr_code", "").strip()
    if not qr:
        raise HTTPException(status_code=400, detail="qr_code required")

    # try existing
    res = await db.execute(select(Skip).where(Skip.qr_code == qr).limit(1))
    obj = res.scalar_one_or_none()
    if obj is None:
        obj = Skip(qr_code=qr, status=SkipStatus.IN_STOCK.value)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)

    return {
        "id": obj.id,
        "qr_code": obj.qr_code,
        "status": obj.status,
        "zone_id": obj.zone_id,
        "created_at": obj.created_at,
    }

@router.get("", dependencies=[Depends(require_admin)])
async def list_skips(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(200, int(limit)))
    res = await db.execute(
        select(Skip).order_by(desc(Skip.created_at)).limit(limit)
    )
    rows = res.scalars().all()
    return [
        {
            "id": s.id,
            "qr_code": s.qr_code,
            "status": s.status,
            "zone_id": s.zone_id,
            "created_at": s.created_at,
        }
        for s in rows
]

@router.get("/by_qr/{qr}", dependencies=[Depends(require_admin)])
async def get_by_qr(qr: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Skip).where(Skip.qr_code == qr).limit(1))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="not found")
    return {
        "id": s.id,
        "qr_code": s.qr_code,
        "status": s.status,
        "zone_id": s.zone_id,
        "created_at": s.created_at,
    }

@router.delete("/{skip_id}", dependencies=[Depends(require_admin)])
async def delete_skip(skip_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Skip).where(Skip.id == skip_id).limit(1))
    s = res.scalar_one_or_none()
    if not s:
        # idempotent delete
        return {"ok": True, "deleted": False}
    s.deleted_at = datetime.utcnow() # soft delete
    await db.commit()
    return {"ok": True, "deleted": True, "id": skip_id}
