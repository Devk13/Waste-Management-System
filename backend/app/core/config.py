# app/core/config.py
from __future__ import annotations
import os, re
from pydantic_settings import BaseSettings, SettingsConfigDict

def _normalize_db_url(url: str | None) -> str | None:
    if not url:
        return url

    # 1) Ensure asyncpg scheme
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    # 2) asyncpg does NOT support "sslmode"; use "ssl=true"
    if "sslmode=" in url:
        url = re.sub(r"sslmode=[^&?#]+", "ssl=true", url)
    elif "ssl=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}ssl=true"

    return url

class Settings(BaseSettings):
    # ... (your existing fields)
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
