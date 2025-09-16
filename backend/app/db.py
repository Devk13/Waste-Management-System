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
    Normalize DATABASE_URL for our async drivers.
    - postgres* -> postgresql+asyncpg and sane ssl/sslmode
    - sqlite*   -> sqlite+aiosqlite while preserving the original '///' slashes
                  and dropping any ssl/sslmode query params
    """
    if not raw:
        return "sqlite+aiosqlite:///./dev.db"

    u = urlparse(raw)
    scheme = u.scheme

    # --- SQLite: preserve slashes and drop ssl flags -------------------------
    if scheme.startswith("sqlite"):
        # Keep the exact path part (e.g., sqlite:///dev.db) but swap driver
        raw_sqlite = (
            raw if raw.startswith("sqlite+aiosqlite:")
            else raw.replace("sqlite:", "sqlite+aiosqlite:", 1)
        )

        # Strip any ssl/sslmode params some envs append globally
        u2 = urlparse(raw_sqlite)
        q = dict(parse_qsl(u2.query, keep_blank_values=True))
        q.pop("ssl", None)
        q.pop("sslmode", None)

        # Rebuild WITHOUT disturbing the path slashes
        return raw_sqlite.split("?", 1)[0] + (("?" + urlencode(q)) if q else "")

    # --- Postgres and others --------------------------------------------------
    # driver selection
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"

    is_asyncpg = scheme.startswith("postgresql+asyncpg")

    # parse and normalize query
    q = dict(parse_qsl(u.query, keep_blank_values=True))

    if is_asyncpg:
        # asyncpg: don't use sslmode; prefer ssl=true if present
        q.pop("sslmode", None)
        v = str(q.get("ssl", "true")).lower()
        if v in ("true", "1", "yes", "on", ""):
            q["ssl"] = "true"
        else:
            q.pop("ssl", None)
    else:
        # psycopg and other sync drivers (local/dev)
        if q.get("ssl") is not None:
            v = str(q["ssl"]).lower()
            if v in ("true", "1", "yes", "on"):
                q.pop("ssl", None)
            else:
                q["sslmode"] = "require"
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
