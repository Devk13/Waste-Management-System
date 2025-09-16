# path: backend/app/db.py
from __future__ import annotations

import os
from typing import Optional
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ---- URL normalizer (handles sqlite/postgres sync→async drivers) -------------

def _to_async_url(raw: Optional[str]) -> str:
    if not raw or raw.strip() == "":
        return "sqlite+aiosqlite:///dev.db"
    url = raw.strip()
    # Render often provides postgres://; convert to asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite://") and "+aiosqlite" not in url:
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


RAW_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "sqlite+aiosqlite:///dev.db"
DB_URL = _to_async_url(RAW_URL)

# ---- Async engine & session factory -----------------------------------------
engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True, future=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# ---- FastAPI dependency (compat shim for existing imports) -------------------
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

__all__ = ["engine", "SessionLocal", "DB_URL", "get_session"]
