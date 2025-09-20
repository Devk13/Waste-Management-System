# path: backend/app/api/admin_bootstrap.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncEngine
from app.db import engine
from app.api.guards import admin_gate

# import your SQLAlchemy Base that has all models registered
try:
    from app.models.base import Base  # adjust to wherever Base.metadata lives
except Exception:
    # fallback: many codebases expose models.Base
    from app.models import Base  # type: ignore

router = APIRouter(prefix="/__admin", tags=["__admin"], dependencies=[Depends(admin_gate)])

@router.post("/bootstrap", status_code=status.HTTP_201_CREATED)
async def bootstrap(db_engine: AsyncEngine = Depends(lambda: engine)):
    """
    ONE-OFF: create tables on an empty database.
    Remove after running once in Render.
    """
    try:
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return {"ok": True, "created": list(Base.metadata.tables.keys())}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"bootstrap_failed: {e.__class__.__name__}: {e}")
