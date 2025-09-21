# ===================================
# backend/app/core/deps.py (admin gate, db session)
# ===================================
from typing import AsyncGenerator
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import ADMIN_API_KEY, DRIVER_API_KEY, DATABASE_URL, EXPOSE_ADMIN_ROUTES

# Single engine/session for the app; wire to your existing ones if present.
engine = create_async_engine(DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False, autocommit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def admin_gate(x_api_key: str = Header(None, alias="X-API-Key")) -> None:
    if not EXPOSE_ADMIN_ROUTES:
        # Why: Avoid accidental admin exposure in prod.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")

async def driver_gate(x_api_key: str = Header(None, alias="X-API-Key")) -> None:
    if x_api_key != DRIVER_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid driver key")
