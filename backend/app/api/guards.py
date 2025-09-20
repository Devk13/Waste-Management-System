from __future__ import annotations
import os
from fastapi import Header, HTTPException

try:
    from app.core.config import settings
except Exception:
    class _S:
        ENV = os.getenv("ENV", "dev")
        ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
    settings = _S()  # type: ignore

IS_PROD = str(getattr(settings, "ENV", "dev")).lower() == "prod"
ADMIN_KEY = os.getenv("ADMIN_API_KEY", getattr(settings, "ADMIN_API_KEY", ""))

async def admin_gate(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not IS_PROD:
        return
    if not ADMIN_KEY or x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin key required")

__all__ = ["admin_gate"]
