# app/core/config.py
from __future__ import annotations
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

def _normalize_db_url(url: str | None) -> str:
    """
    Render can inject:
      - postgres://USER:PASS@HOST/DB
      - postgresql://USER:PASS@HOST/DB
    SQLAlchemy async wants:
      - postgresql+asyncpg://USER:PASS@HOST/DB?sslmode=require
    """
    if not url:
        return "sqlite+aiosqlite:///./dev.db"

    u = url.strip()

    if u.startswith("postgres://"):
        u = "postgresql+asyncpg://" + u[len("postgres://"):]
    elif u.startswith("postgresql://"):
        # convert only if not already async
        if not u.startswith("postgresql+asyncpg://"):
            u = "postgresql+asyncpg://" + u[len("postgresql://"):]

    # ensure sslmode=require for Render-managed Postgres
    if u.startswith("postgresql+asyncpg://") and "sslmode=" not in u:
        sep = "&" if "?" in u else "?"
        u = f"{u}{sep}sslmode=require"

    return u


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

# normalize DATABASE_URL coming from env (Render gives postgres:/postgresql:…)
settings.DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL") or settings.DATABASE_URL)
