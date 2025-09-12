# path: backend/app/api/routes.py
from __future__ import annotations
from fastapi import APIRouter

router = APIRouter()

from app.api import skips as skips_api
router.include_router(skips_api.router)

def _try_include(modpath: str, attr: str = "router") -> bool:
    """
    Try to import `modpath` and include its `attr` (router).
    If anything fails, print a small note and continue.
    """
    try:
        mod = __import__(modpath, fromlist=[attr])
        router.include_router(getattr(mod, attr))
        print(f"[routes] mounted {modpath}")
        return True
    except Exception as e:  # pragma: no cover
        print(f"[routes] skipping {modpath}: {e}")
        return False


# --- required: your skips endpoints (use whatever name you actually export) ---
# Try both common names, so this works no matter if your file exposes `router`
# or `api_router`.
if not (_try_include("app.api.skips", "router") or _try_include("app.api.skips", "api_router")):
    print("[routes] WARNING: could not mount app.api.skips")

# optional modules
_optional = [
    ("app.api.driver", "router"),
    ("app.api.dispatch", "router"),
    ("app.api.drivers", "router"),
]
for modpath, attr in _optional:
    try:
        mod = __import__(modpath, fromlist=[attr])
        router.include_router(getattr(mod, attr))
    except Exception:
        continue

