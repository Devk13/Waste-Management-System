# path: backend/app/api/routes.py
from __future__ import annotations
import logging
import os
from importlib import import_module
from fastapi import APIRouter
from app.core.config import settings

log = logging.getLogger(__name__)
api_router = APIRouter()
router = APIRouter()
print("[routes] boot", flush=True)  # proves routes.py imported

# --- existing driver routes
from .driver import router as driver_router
router.include_router(driver_router, tags=["driver"])

# --- tiny helper to mount routers by module path (keeps startup resilient)
def _try_include(module_path: str, prefix: str = "", tags: list[str] | None = None):
    try:
        mod = import_module(module_path)
        r = getattr(mod, "router", None)
        if r is None:
            raise RuntimeError("module has no 'router'")
        router.include_router(r, prefix=prefix, tags=tags or [])
        print(f"[routes] mounted {module_path}", flush=True)
    except Exception as e:
        print(f"[routes] skipping {module_path}: {e}", flush=True)

def _safe_include(prefix: str, import_path: str, tag: str | None = None) -> None:
    """Guard router imports so optional modules don't crash startup."""
    try:
        module = __import__(import_path, fromlist=["router"])
        kwargs = {"prefix": prefix}
        if tag:
            kwargs["tags"] = [tag]
        api_router.include_router(module.router, **kwargs)
        log.info("Mounted %s at %s", import_path, prefix)
    except Exception as exc:  # pragma: no cover
        log.warning("Skipped %s at %s: %s", import_path, prefix, exc)


# Core routers already in your app
_safe_include("/driver", "app.api.driver", "driver")
_safe_include("/skips", "app.api.skips", "skips")

# Smoke/debug helpers (safe to include always)
_safe_include("/skips", "app.api.skips_smoke", "skips")
_safe_include("", "app.api.debug_routes", "__debug")

# --- admin/demo routes gate (env flag)
# accepts: true/1/yes (case-insensitive). Reads from settings, falls back to raw env.
_EXPOSE = str(getattr(settings, "EXPOSE_ADMIN_ROUTES", os.getenv("EXPOSE_ADMIN_ROUTES", "false"))).lower() in ("1", "true", "yes")

print(f"[routes] flag trace | env={os.getenv('EXPOSE_ADMIN_ROUTES')} "
      f"| settings={getattr(settings, 'EXPOSE_ADMIN_ROUTES', None)} "
      f"| resolved={_EXPOSE}", flush=True)

if _EXPOSE:
    try:
        from .skips_demo import router as admin_skips_router
        # Give it an explicit tag so it appears as "admin-skips" in /docs
        router.include_router(admin_skips_router, tags=["admin-skips"])
        print("[routes] mounted admin skips demo", flush=True)
    except Exception as e:
        print(f"[routes] skipping admin skips demo: {e}", flush=True)
else:
    print("[routes] admin skips demo disabled", flush=True)

# --- normal app routers
_try_include("app.api.skips", prefix="/skips", tags=["skips"])
# add more when ready...
print("[routes] ready", flush=True)