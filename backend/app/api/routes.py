# path: backend/app/api/routes.py
from __future__ import annotations

import os
import logging
from importlib import import_module
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, Body, Depends, Header, HTTPException
from pydantic import BaseModel

try:
    from app.core.config import settings  # type: ignore[attr-defined]
except Exception:
    class _S:
        EXPOSE_ADMIN_ROUTES = False
        ENV = "dev"
        ADMIN_API_KEY = "super-temp-seed-key"
    settings = _S()  # type: ignore

log = logging.getLogger(__name__)

api_router = APIRouter()
__mount_report__: List[Dict[str, Any]] = []

def _safe_include(prefix: str, import_path: str, tag: Optional[str] = None) -> None:
    try:
        module = import_module(import_path)
        kwargs = {"prefix": prefix}
        if tag:
            kwargs["tags"] = [tag]
        api_router.include_router(getattr(module, "router"), **kwargs)  # type: ignore[attr-defined]
        __mount_report__.append({"module": import_path, "prefix": prefix, "ok": True})
        log.info("Mounted %s at %s", import_path, prefix)
    except Exception as exc:
        __mount_report__.append({"module": import_path, "prefix": prefix, "ok": False, "error": str(exc)})
        log.warning("Skipped %s at %s: %s", import_path, prefix, exc)

IS_PROD = str(getattr(settings, "ENV", "dev")).lower() == "prod"
ADMIN_KEY = str(getattr(settings, "ADMIN_API_KEY", ""))

# --- admin gate: only enforced in prod ---------------------------------------
def admin_gate(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not IS_PROD:
        return
    if not ADMIN_KEY or x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin key required")

# --- Core routers (single pass) ----------------------------------------------
_safe_include("/driver", "app.api.driver", "driver")
if not IS_PROD:
    _safe_include("/driver/dev", "app.api.dev", "dev")  # hidden in prod
_safe_include("/skips", "app.api.skips", "skips")
_safe_include("/skips", "app.api.skips_smoke", "skips")
_safe_include("", "app.api.driver_schedule", "driver:schedule")
_safe_include("", "app.api.wtn", "wtn")
_safe_include("", "app.api.meta", "__meta")
_safe_include("", "app.api.wtn_debug", "__debug")

# --- helpers: bool flag resolver with trace -----------------------------------
def _flag(name: str, default: str = "false") -> bool:
    """Resolve 'true/1/yes/on' style env or settings values to bool, with trace."""
    raw = os.getenv(name, default)
    try:
        from app.core.config import settings  # type: ignore
        raw = str(getattr(settings, name, raw))
    except Exception:
        pass
    val = str(raw).strip().lower() in {"1", "true", "yes", "on"}
    print(f"[routes] flag {name} | raw={raw!r} -> {val}", flush=True)
    return val

# --- Admin routers (gated by env var) ----------------------------------------
_EXPOSE = _flag("EXPOSE_ADMIN_ROUTES", "false")
if _EXPOSE:
    _safe_include("", "app.api.admin_contractors", "admin:contractors")
    _safe_include("", "app.api.admin_vehicles", "admin:vehicles")
    _safe_include("", "app.api.admin_drivers", "admin:drivers")
    _safe_include("", "app.api.admin_bin_assignments", "admin:bins")
else:
    log.info("Admin routes disabled (EXPOSE_ADMIN_ROUTES=false)")

# --- Meta + Debug ------------------------------------------------------------
@api_router.get("/_meta/ping", tags=["__meta"])
async def meta_ping() -> Dict[str, str]:
    return {"pong": "ok"}

@api_router.get("/_debug/mounts", tags=["__debug"], dependencies=[Depends(admin_gate)])
async def debug_mounts() -> List[Dict[str, Any]]:
    return __mount_report__

@api_router.get("/_debug/routes", tags=["__debug"], dependencies=[Depends(admin_gate)])
async def debug_routes(request: Request) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in request.app.router.routes:
        methods = sorted(getattr(r, "methods", []) or [])
        out.append({"path": r.path, "name": getattr(r, "name", ""), "methods": methods})
    return out

# tolerant dev seed fallback (kept as before)
class EnsureSkipResult(BaseModel):
    skip_id: str = "DEV-SKIP-001"
    note: str = "Seeded (dev only)"

@api_router.api_route("/driver/dev/ensure-skip", methods=["GET", "POST"], tags=["dev"])
async def ensure_skip_dev_fallback() -> EnsureSkipResult:
    # If not mounted via app.api.dev, only expose in non-prod
    if IS_PROD:
        raise HTTPException(status_code=404, detail="Not found")
    return EnsureSkipResult()

__all__ = ["api_router", "__mount_report__"]
