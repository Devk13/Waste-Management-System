# path: backend/app/api/routes.py
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# --- Always-on routers -------------------------------------------------------
# /skips must always be present for the app to work
from app.api import skips as skips_api  # noqa: E402  (import after router is OK)
router.include_router(skips_api.router)


# --- Optional routers (included only if the module exists) -------------------
# This keeps prod running even if a feature module hasn't been created yet.

def _include_optional(modpath: str, attr: str = "router") -> None:
    """Import `modpath` and include its `router` if present.

    Using try/except keeps things resilient during development while still
    being explicit about what we might include.
    """
    try:
        mod = __import__(modpath, fromlist=[attr])
        router.include_router(getattr(mod, attr))
    except Exception:  # ImportError, AttributeError, etc. — safe to skip
        pass


# Legacy driver endpoints (if you still have them)
_include_optional("app.api.driver")

# Legacy dispatch endpoints (if you still have them)
_include_optional("app.api.dispatch")

# New drivers module that provides /drivers/me
_include_optional("app.api.drivers")
