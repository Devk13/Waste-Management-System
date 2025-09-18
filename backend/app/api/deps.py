# path: backend/app/api/deps.py
from __future__ import annotations

import os
from typing import AsyncIterator, Optional, Dict, Any

from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import engine
try:
    # optional; we read ENV/admin key from settings if present
    from app.core.config import settings  # type: ignore
except Exception:
    settings = None  # type: ignore

# --- DB session dependency ------------------------------------------------------

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an AsyncSession and ensure it closes cleanly."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# --- Auth: simple admin stub ----------------------------------------------------

async def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
) -> Dict[str, Any]:
    """
    Minimal admin/auth dependency:

    - DEV/TEST (ENV != 'prod'): returns a fake admin user.
    - PROD: requires ADMIN_API_KEY to match either X-Admin-Key (preferred)
            or X-API-Key (fallback). Returns an admin identity or 401.

    This is intentionally simple so routers like app.api.skips can import.
    Replace with real auth later (JWT, sessions, etc.).
    """
    env = (os.getenv("ENV") or getattr(settings, "ENV", "dev") if settings else "dev").lower()
    if env != "prod":
        return {"id": "dev-admin", "role": "admin", "env": env}

    expected = (
        os.getenv("ADMIN_API_KEY")
        or (getattr(settings, "ADMIN_API_KEY", "") if settings else "")
    )

    # If no admin key is configured in prod, allow but warn (avoid lockout)
    if not expected:
        return {"id": "admin", "role": "admin", "note": "no ADMIN_API_KEY configured"}

    supplied = x_admin_key or x_api_key
    if supplied and supplied == expected:
        return {"id": "admin", "role": "admin"}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

__all__ = ["get_db", "get_current_user"]
