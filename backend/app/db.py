# path: backend/app/db.py
from __future__ import annotations

import os
import ssl
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine

# Fallback settings stub (avoid circular import at boot)
try:
    from app.core.config import settings  # type: ignore
except Exception:
    class _S:
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    settings = _S()  # type: ignore

_VALID_SSLMODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}


def _normalize_database_url(raw: str) -> str:
    """
    Normalize DATABASE_URL to an async SQLAlchemy URL.

    - postgres/postgresql -> postgresql+asyncpg
    - sqlite              -> sqlite+aiosqlite
    - asyncpg driver      -> drop sslmode, prefer ?ssl=true
    - psycopg driver      -> map ssl=true -> sslmode=require, validate sslmode
    """
    if not raw:
        return "sqlite+aiosqlite:///dev.db"

    u = urlparse(raw)
    scheme = u.scheme

    # Scheme → async driver
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"
    elif scheme.startswith("sqlite"):
        scheme = "sqlite+aiosqlite"
    # else: keep explicit driver if already set (postgresql+asyncpg / postgresql+psycopg etc.)

    is_asyncpg = scheme.startswith("postgresql+asyncpg")

    q = dict(parse_qsl(u.query, keep_blank_values=True))

    if is_asyncpg:
        # asyncpg must not receive sslmode; use ssl=true
        q.pop("sslmode", None)
        v = str(q.get("ssl", "true")).lower()
        if v in ("true", "1", "yes", "on", ""):
            q["ssl"] = "true"
        else:
            q.pop("ssl", None)
    else:
        # psycopg: accept ssl=true → sslmode=require; validate/normalize sslmode
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


# Resolve and normalize URL
_RAW_URL = os.getenv("DATABASE_URL", getattr(settings, "DATABASE_URL", ""))
DB_URL: str = _normalize_database_url(_RAW_URL)

# Build connect args (explicit SSLContext for asyncpg)
connect_args: dict = {}
try:
    url = make_url(DB_URL)
    if url.drivername.startswith("postgresql+asyncpg"):
        # Prefer verified context with certifi (works on slim images)
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            ctx = ssl.create_default_context()
        # Allow opt-out of verification if needed: DB_SSL_VERIFY=0
        if os.getenv("DB_SSL_VERIFY", "1").lower() in ("0", "false", "no"):
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx  # asyncpg expects the SSLContext under key 'ssl'
except Exception:
    pass

# Shared async engine
engine = create_async_engine(DB_URL, echo=False, pool_pre_ping=True, connect_args=connect_args)

__all__ = ["engine", "DB_URL"]
