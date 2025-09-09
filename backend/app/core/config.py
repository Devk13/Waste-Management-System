from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py
import os  # keep if you already have it

def _normalize_db_url(url: str) -> str:
    # Convert Render-style "postgres://..." to async SQLAlchemy URL
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    # Ensure sslmode=require is present for Render’s managed Postgres
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
