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
    """Normalize DATABASE_URL to an async SQLAlchemy URL.
    - postgres -> postgresql+asyncpg
    - sqlite   -> sqlite+aiosqlite
    - coerce ssl=true  or sslmode=true -> sslmode=require
    - ensure sslmode=require when using Postgres and none provided
    """
    if not raw:
        return "sqlite+aiosqlite:///dev.db"

    u = urlparse(raw)
    scheme = u.scheme

    # Scheme fixes
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"
    elif scheme.startswith("postgresql+"):
        # leave as-is (may already be asyncpg)
        pass
    elif scheme.startswith("sqlite"):
        scheme = "sqlite+aiosqlite"

    # Query fixes
    q = dict(parse_qsl(u.query, keep_blank_values=True))

    # Accept providers that pass ssl=true
    if q.get("ssl") is not None:
        if str(q.get("ssl")).lower() in ("true", "1", "yes", "on"):
            q.pop("ssl", None)
            q["sslmode"] = "require"
        else:
            q.pop("ssl", None)

    # Coerce bad sslmode values like 'true' -> 'require'
    if "sslmode" in q:
        v = str(q["sslmode"]).lower()
        if v in ("true", "1", "yes", "on", ""):  # provider oddities
            q["sslmode"] = "require"
        elif v not in _VALID_SSLMODES:
            q["sslmode"] = "require"
    else:
        # Default to require on Postgres
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
