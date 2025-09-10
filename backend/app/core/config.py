# app/core/config.py (replace the normalizer with this)
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

def _normalize_db_url(url: str | None) -> str | None:
    if not url:
        return url

    # 1) Render gives 'postgres://...' -> we need 'postgresql+asyncpg://...'
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]

    # 2) If it has sslmode, map to asyncpg's 'ssl=true'
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    if "sslmode" in q:
        # drop sslmode and use asyncpg's 'ssl=true'
        q.pop("sslmode", None)
        q["ssl"] = "true"
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))

    # 3) If no SSL query param at all, enforce it
    if "ssl=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}ssl=true"

    return url

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    JWT_SECRET: str = "dev"
    DRIVER_QR_BASE_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "*"

    # optional debug helpers you added:
    DEBUG_FAKE_ROLE: str | None = None
    DEBUG_FAKE_USER_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()

# Normalize whatever is in env (or default)
settings.DATABASE_URL = _normalize_db_url(os.getenv("DATABASE_URL", settings.DATABASE_URL))
