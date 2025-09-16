# path: backend/app/db.py
from __future__ import annotations

import os
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from sqlalchemy.ext.asyncio import create_async_engine

# Prefer settings if available, but fall back to env for Render
try:  # local import guard (avoid circulars at tooling time)
    from app.core.config import settings  # type: ignore
except Exception:  # pragma: no cover - during early tooling
    class _S:  # minimal stub
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    settings = _S()  # type: ignore


# ------------------------------------------------------------
# URL normalizer for Render/Heroku-style Postgres URLs
# ------------------------------------------------------------

_VALID_SSLMODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}

def _normalize_database_url(raw: str) -> str:
    """
    Normalize DATABASE_URL to an async SQLAlchemy URL.

    - postgres       -> postgresql+asyncpg
    - sqlite         -> sqlite+aiosqlite
    - asyncpg driver -> use `ssl=true` (drop any sslmode)
    - psycopg driver -> accept `ssl=true` and convert to `sslmode=require`
    """
    if not raw:
        return "sqlite+aiosqlite:///dev.db"

    u = urlparse(raw)
    scheme = u.scheme

    # Scheme fixes
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"
    elif scheme.startswith("postgresql+"):
        pass  # already explicit driver
    elif scheme.startswith("sqlite"):
        scheme = "sqlite+aiosqlite"

    is_asyncpg = scheme.startswith("postgresql+asyncpg")

    # Query params
    q = dict(parse_qsl(u.query, keep_blank_values=True))

    if is_asyncpg:
        # --- asyncpg: must NOT pass sslmode; should pass ssl=true
        q.pop("sslmode", None)
        v = str(q.get("ssl", "true")).lower()
        if v in ("true", "1", "yes", "on", ""):
            q["ssl"] = "true"
        else:
            q.pop("ssl", None)  # explicitly false -> no ssl param
    else:
        # --- psycopg/other: map ssl=true to sslmode=require and validate sslmode
        if q.get("ssl") is not None:
            if str(q["ssl"]).lower() in ("true", "1", "yes", "on"):
                q.pop("ssl", None)
                q["sslmode"] = "require"
            else:
                q.pop("ssl", None)

        if "sslmode" in q:
            v = str(q["sslmode"]).lower()
            if v in ("true", "1", "yes", "on", "") or v not in _VALID_SSLMODES:
                q["sslmode"] = "require"
        else:
            if scheme.startswith("postgresql"):
                q["sslmode"] = "require"

    new = u._replace(scheme=scheme, query=urlencode(q))
    return urlunparse(new)


# Prefer env var in Render, fall back to settings
_RAW_URL = os.getenv("DATABASE_URL", getattr(settings, "DATABASE_URL", ""))
DB_URL: str = _normalize_database_url(_RAW_URL)

# Shared async engine
engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True)

__all__ = ["engine", "DB_URL"]
