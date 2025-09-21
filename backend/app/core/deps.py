# path: backend/app/core/deps.py

from typing import AsyncGenerator
from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Use settings instead of module-level constants
from .config import settings

# Single engine/session for the app; shared across routers
engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False, autocommit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def admin_gate(x_api_key: str = Header(None, alias="X-API-Key")) -> None:
    # Why: avoid accidental admin exposure in prod
    if not settings.EXPOSE_ADMIN_ROUTES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")

async def driver_gate(x_api_key: str = Header(None, alias="X-API-Key")) -> None:
    if x_api_key != settings.DRIVER_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid driver key")
