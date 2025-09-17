from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db

# why: make this endpoint resilient even if models evolve
try:
    from app.models import Skip, SkipPlacement, SkipMovement
except Exception:
    Skip = SkipPlacement = SkipMovement = None  # type: ignore

router = APIRouter(tags=["skips"])

@router.get("/__smoke")
async def skips_smoke(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    out: Dict[str, Any] = {"ok": True}
    try:
        if Skip is not None:
            out["skips"] = (await db.execute(select(func.count()).select_from(Skip))).scalar_one()
        if SkipPlacement is not None:
            out["placements"] = (await db.execute(select(func.count()).select_from(SkipPlacement))).scalar_one()
        if SkipMovement is not None:
            out["movements"] = (await db.execute(select(func.count()).select_from(SkipMovement))).scalar_one()
    except Exception as e:
        out["ok"] = False
        out["error"] = f"{type(e).__name__}: {e}"
    return out
