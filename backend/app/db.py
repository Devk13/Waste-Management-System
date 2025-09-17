# path: backend/app/db.py
from __future__ import annotations

import os
import ssl
from pathlib import Path
from typing import Dict, Optional

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine


# ---- helpers ----------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = (APP_DIR / "dev.db").resolve().as_posix()  # absolute

def _normalize_raw(raw: Optional[str]) -> Optional[str]:
    """Normalize string URL for async drivers; return None if unusable."""
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None

    # postgres → asyncpg
    if s.startswith("postgres://"):
        s = s.replace("postgres://", "postgresql+asyncpg://", 1)
    elif s.startswith("postgresql://") and "+asyncpg" not in s:
        s = s.replace("postgresql://", "postgresql+asyncpg://", 1)

    # sqlite → aiosqlite
    if s.startswith("sqlite://") and "+aiosqlite" not in s:
        s = s.replace("sqlite://", "sqlite+aiosqlite://", 1)

    return s


def _build_url() -> URL:
    """Single source of truth for DB URL."""
    # env or settings
    try:
        from app.core.config import settings  # optional
        cand = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
    except Exception:
        cand = os.getenv("DATABASE_URL")

    s = _normalize_raw(cand)

    if not s:
        # absolute SQLite fallback
        return URL.create(drivername="sqlite+aiosqlite", database=DEFAULT_SQLITE_PATH)

    # parse robustly; if parsing fails, fall back to SQLite
    try:
        return make_url(s)
    except Exception:
        return URL.create(drivername="sqlite+aiosqlite", database=DEFAULT_SQLITE_PATH)


def _build_connect_args(url: URL) -> Dict[str, object]:
    """Only what’s needed; asyncpg gets an SSLContext if available."""
    if url.get_backend_name().startswith("sqlite"):
        return {"timeout": 30}
    if url.get_backend_name().startswith("postgresql") and "asyncpg" in (url.get_driver_name() or ""):
        ctx = None
        try:
            import certifi  # type: ignore
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            ctx = ssl.create_default_context()
        # allow opt-out in dev: DB_SSL_VERIFY=0
        if str(os.getenv("DB_SSL_VERIFY", "1")).lower() in {"0", "false", "no"}:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return {"ssl": ctx}
    return {}  # other drivers: defaults


# ---- build URL + engine -----------------------------------------------------

DB_URL: URL = _build_url()
print(f"[db] Using DB_URL = {repr(DB_URL)}", flush=True)  # easy triage (Render/local)

connect_args = _build_connect_args(DB_URL)
engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True, connect_args=connect_args)

__all__ = ["engine", "DB_URL"]
