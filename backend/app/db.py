# path: backend/app/db.py
from __future__ import annotations

import os
import ssl
from pathlib import Path
from typing import Dict, Optional, AsyncGenerator

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# ---- helpers ----------------------------------------------------------------
APP_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = (APP_DIR / "dev.db").resolve().as_posix()

def _normalize_raw(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None
    if s.startswith("postgres://"):
        s = s.replace("postgres://", "postgresql+asyncpg://", 1)
    elif s.startswith("postgresql://") and "+asyncpg" not in s:
        s = s.replace("postgresql://", "postgresql+asyncpg://", 1)
    if s.startswith("sqlite://") and "+aiosqlite" not in s:
        s = s.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return s

def _build_url() -> URL:
    try:
        from app.core.config import settings  # type: ignore
        cand = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
    except Exception:
        cand = os.getenv("DATABASE_URL")
    s = _normalize_raw(cand)
    if not s:
        return URL.create(drivername="sqlite+aiosqlite", database=DEFAULT_SQLITE_PATH)
    try:
        return make_url(s)
    except Exception:
        return URL.create(drivername="sqlite+aiosqlite", database=DEFAULT_SQLITE_PATH)

def _build_connect_args(url: URL) -> Dict[str, object]:
    if url.get_backend_name().startswith("sqlite"):
        return {"timeout": 30}
    if url.get_backend_name().startswith("postgresql") and "asyncpg" in (url.get_driver_name() or ""):
        try:
            import certifi  # type: ignore
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            ctx = ssl.create_default_context()
        if str(os.getenv("DB_SSL_VERIFY", "1")).lower() in {"0", "false", "no"}:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return {"ssl": ctx}
    return {}

# ---- engine -----------------------------------------------------------------
DB_URL: URL = _build_url()
print(f"[db] Using DB_URL = {repr(DB_URL)}", flush=True)

connect_args = _build_connect_args(DB_URL)
engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True, connect_args=connect_args)

# ---- Base shim (so `from app.db import Base` works) --------------------------
try:
    # prefer your declared Base if exported from models package
    from app.models import models as _m  # type: ignore
    Base = getattr(_m, "Base")  # type: ignore[attr-defined]
except Exception:
    try:
        from app.models import Base  # type: ignore  # already exported at package root?
    except Exception:
        # final fallback: define a DeclarativeBase for tests
        from sqlalchemy.orm import DeclarativeBase
        class Base(DeclarativeBase):  # type: ignore[no-redef]
            pass

# ---- Optional: session factory for tests/utilities ---------------------------
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Optional DI helper; tests can import from app.db if needed."""
    async with AsyncSessionLocal() as session:
        yield session

__all__ = ["engine", "DB_URL", "Base", "AsyncSessionLocal", "get_db"]
