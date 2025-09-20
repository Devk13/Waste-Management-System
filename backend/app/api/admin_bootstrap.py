# path: backend/app/api/admin_bootstrap.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.guards import admin_gate
from app.db import engine

# Resolve Base.metadata robustly
try:
    from app.models.base import Base  # preferred
except Exception:  # pragma: no cover
    from app.models import Base  # fallback, if your project exposes Base here

router = APIRouter(prefix="/__admin", tags=["__admin"])

@router.post("/bootstrap", dependencies=[Depends(admin_gate)])
async def bootstrap() -> dict[str, str]:
    """Idempotently create DB tables for all mapped models."""
    eng: AsyncEngine = engine
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return {"ok": "created"}
