# path: backend/app/core/deps.py
from typing import AsyncGenerator
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from urllib.parse import urlsplit, parse_qsl, urlunsplit
from .config import settings

def _force_asyncpg_clean(url: str) -> str:
    """
    Ensure postgresql+asyncpg and strip ssl/sslmode from the query (we pass SSL via connect_args).
    """
    if not url:
        return url
    u = urlsplit(url)
    # force asyncpg dialect
    scheme = u.scheme
    if scheme.startswith("postgres"):
        scheme = "postgresql+asyncpg"
    # drop ssl and sslmode params
    q = dict(parse_qsl(u.query, keep_blank_values=True))
    q.pop("ssl", None)
    q.pop("sslmode", None)
    return urlunsplit((scheme, u.netloc, u.path, "", u.fragment))

DB_URL = _force_asyncpg_clean(settings.DATABASE_URL)

# require TLS explicitly for asyncpg
engine = create_async_engine(
    DB_URL,
    future=True,
    echo=False,
    connect_args={"ssl": True},  # avoids url ssl/sslmode ambiguity
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False, autocommit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def admin_gate(x_api_key: str = Header(None, alias="X-API-Key")) -> None:
    if not settings.EXPOSE_ADMIN_ROUTES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")

async def driver_gate(x_api_key: str = Header(None, alias="X-API-Key")) -> None:
    if x_api_key != settings.DRIVER_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid driver key")
