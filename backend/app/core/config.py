# path: backend/app/core/config.py
from __future__ import annotations

import os
from typing import Optional
from pydantic import BaseSettings, AnyHttpUrl


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    CORS_ORIGINS: str = "*"  # comma-separated allowed origins or "*"
    DRIVER_QR_BASE_URL: Optional[AnyHttpUrl] = None  # e.g. https://driver.example.com

    class Config:
        env_file = ".env"


# Allow overriding env file via ENV_FILE if needed
settings = Settings(_env_file=os.getenv("ENV_FILE", ".env"))
