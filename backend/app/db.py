# backend/app/db.py
from __future__ import annotations
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

DB_URL = settings.DATABASE_URL

# Render’s managed Postgres with asyncpg needs `ssl=True` (not sslmode)
connect_args = {}
if DB_URL.startswith("postgresql+asyncpg://") and "ssl=" not in DB_URL:
    connect_args["ssl"] = True  # safe default for managed Postgres

engine = create_async_engine(
    DB_URL,
    future=True,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
