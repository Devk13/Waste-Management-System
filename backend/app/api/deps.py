# ================================
# file: backend/app/api/deps.py
# (Minimal, cycle-free dependency)
# ================================
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db import engine  # only dependency

# Single factory for async sessions (no ORM imports, no routers)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Why: provide DB session without importing any app.api.* modules
    async with SessionLocal() as session:
        yield session

