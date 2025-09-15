# path: backend/app/db.py
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Read from config (do not hard-code the URL here)
DB_URL = settings.DATABASE_URL

# Render Postgres with asyncpg wants ssl=True; add it if the URL lacks it
connect_args: dict = {}
if DB_URL.startswith("postgresql+asyncpg://") and "ssl=" not in DB_URL:
    connect_args["ssl"] = True  # safe default for managed Postgres

engine: AsyncEngine = create_async_engine(
    DB_URL,
    future=True,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args or None,
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an AsyncSession per request."""
    async with SessionLocal() as session:
        yield session
