from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py
import os

def _normalize_db_url(url: str) -> str:
    # Convert Render-style postgres URLs to async SQLAlchemy URL
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    # Ensure sslmode=require for Render managed Postgres
    if "sslmode=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"
    return url

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    JWT_SECRET: str = "dev"
    DRIVER_QR_BASE_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "*"

    DEBUG_FAKE_ROLE: str | None = None       # e.g. "admin" or "driver"
    DEBUG_FAKE_USER_ID: str | None = None    # UUID string; optional

    # why: pydantic v2 uses SettingsConfigDict instead of inner Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()

# normalize DATABASE_URL coming from env (Render gives postgres://…)
settings.DATABASE_URL = _normalize_db_url(
    os.getenv("DATABASE_URL", settings.DATABASE_URL)
)
