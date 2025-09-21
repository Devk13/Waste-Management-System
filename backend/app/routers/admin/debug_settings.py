# path: backend/app/routers/admin/debug_settings.py

from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlparse, parse_qs

from fastapi import APIRouter, Depends, Request

from app.core.config import settings, CORS_ORIGINS_LIST
from app.core.deps import admin_gate
from app.db import DB_URL

router = APIRouter(
    prefix="",
    tags=["__debug"],
    dependencies=[Depends(admin_gate)],  # why: admin-only
)

def _mask(s: str | None) -> str:
    if not s:
        return ""
    return s[:2] + "…" + s[-2:] if len(s) > 6 else "***"

@router.get("/__debug/settings")
def __debug_settings(request: Request) -> Dict[str, Any]:
    # CORS (effective per config; browsers reject '*' with credentials)
    wildcard = (CORS_ORIGINS_LIST == ["*"]) or ("*" in CORS_ORIGINS_LIST)
    allow_creds = bool(getattr(settings, "CORS_ALLOW_CREDENTIALS", False)) and not wildcard
    allow_origins = ["*"] if wildcard else CORS_ORIGINS_LIST

    # DB summary (no secrets)
    u = urlparse(DB_URL)
    q = parse_qs(u.query)
    db_info = {
        "scheme": u.scheme,
        "host": u.hostname,
        "ssl": q.get("ssl", [""])[0] or q.get("sslmode", [""])[0] or "",
    }

    # Mounted routes (presence only)
    paths = {getattr(r, "path", "") for r in request.app.routes}
    routes_info = {
        "admin_jobs_mounted": any(p.startswith("/admin/jobs") for p in paths),
        "driver_schedule_mounted": "/driver/schedule" in paths and "/driver/schedule/{task_id}/done" in paths,
        "debug_routes": "/__debug/routes" in paths,
        "debug_mounts": "/__debug/mounts" in paths,
    }

    return {
        "env": getattr(settings, "ENV", "dev"),
        "debug": bool(getattr(settings, "DEBUG", False)),
        "expose_admin_routes": bool(getattr(settings, "EXPOSE_ADMIN_ROUTES", False)),
        "driver_qr_base_url": getattr(settings, "DRIVER_QR_BASE_URL", ""),
        "cors": {
            "origins_list": CORS_ORIGINS_LIST,
            "wildcard": wildcard,
            "allow_credentials_effective": allow_creds,
            "allow_origins_effective": allow_origins,
        },
        "keys": {
            "admin_api_key_masked": _mask(getattr(settings, "ADMIN_API_KEY", "")),
            "driver_api_key_masked": _mask(getattr(settings, "DRIVER_API_KEY", "")),
            "admin_api_key_set": bool(getattr(settings, "ADMIN_API_KEY", "")),
            "driver_api_key_set": bool(getattr(settings, "DRIVER_API_KEY", "")),
        },
        "db": db_info,
        "routes": routes_info,
    }
