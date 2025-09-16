# path: backend/app/api/routes.py
from __future__ import annotations

from importlib import import_module
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

from .driver import router as driver_router
router.include_router(driver_router, tags=["driver"])


def _try_include(module_path: str, prefix: str = "", tags: list[str] | None = None):
    try:
        mod = import_module(module_path)
        r = getattr(mod, "router", None)
        if r is None:
            raise RuntimeError("module has no 'router'")
        router.include_router(r, prefix=prefix, tags=tags or [])
        print(f"[routes] mounted {module_path}")
    except Exception as e:  # keep startup resilient
        print(f"[routes] skipping {module_path}: {e}")

# Admin/demo routes — gated
if str(getattr(settings, "EXPOSE_ADMIN_ROUTES", "false")).lower() in ("1", "true", "yes"):
    try:
        from .skips_demo import router as admin_skips_router
        router.include_router(admin_skips_router)
        print("[routes] mounted admin skips demo", flush=True)
    except Exception as e:
        print(f"[routes] skipping admin skips demo: {e}", flush=True)

# Keep only the routers we actually use
_try_include("app.api.skips", prefix="/skips", tags=["skips"])      # your existing skips API
_try_include("app.api.driver", prefix="/driver", tags=["driver"])    # new driver flow

# Remove/omit fragile includes that spam logs (dispatch/drivers, etc.)
# Add other routers here when they are ready.
