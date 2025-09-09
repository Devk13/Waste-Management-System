# path: backend/app/db.py
from __future__ import annotations
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

# Load DB URL from settings when available; fall back to local SQLite.
try:
    from app.core.config import settings  # type: ignore
    DB_URL = getattr(settings, "DATABASE_URL", None) or "sqlite+aiosqlite:///./dev.db"
except Exception:  # pragma: no cover
    DB_URL = "sqlite+aiosqlite:///./dev.db"

Base = declarative_base()
engine: AsyncEngine = create_async_engine(DB_URL, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
