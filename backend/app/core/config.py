# backend/app/core/config.py
from __future__ import annotations
import os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_db_url(raw: str) -> str:
    """
    Accepts Render postgres URLs like:
      postgres://user:pass@host:5432/db?sslmode=require
    and converts to asyncpg form:
      postgresql+asyncpg://user:pass@host:5432/db?ssl=true
    """
    if not raw:
        return raw

    u = urlparse(raw)

    # 1) scheme -> asyncpg
    scheme = u.scheme
    if scheme.startswith("postgres"):
        scheme = "postgresql+asyncpg"

    # 2) query params
    q = dict(parse_qsl(u.query, keep_blank_values=True))

    # Render often sends sslmode=require; asyncpg wants ssl=true
    if "sslmode" in q:
        # keep a record if you like: q.pop("sslmode")
        q.pop("sslmode", None)
        q.setdefault("ssl", "true")

    # If nothing set, still enforce ssl for managed DBs
    q.setdefault("ssl", "true")

    # Rebuild
    new = u._replace(scheme=scheme, query=urlencode(q))
    return urlunparse(new)


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    JWT_SECRET: str = "dev"
    DRIVER_QR_BASE_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
settings.DATABASE_URL = _normalize_db_url(
    os.getenv("DATABASE_URL", settings.DATABASE_URL)
)
