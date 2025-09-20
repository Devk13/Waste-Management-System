# path: backend/app/api/admin_bootstrap.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncEngine
from app.db import engine
from app.api.guards import admin_gate
from app.models import Base
from app.api.admin_bin_assignments import assign_bin

# import your SQLAlchemy Base that has all models registered
try:
    from app.models.base import Base  # adjust to wherever Base.metadata lives
except Exception:
    # fallback: many codebases expose models.Base
    from app.models import Base  # type: ignore

router = APIRouter(prefix="/__admin", tags=["__admin"])

@router.post("/bootstrap", dependencies=[Depends(admin_gate)])
async def bootstrap(_: None = Depends(admin_gate)) -> dict[str, str]:
    # Create all tables (idempotent)
    eng: AsyncEngine = engine
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return {"ok": "created"}
