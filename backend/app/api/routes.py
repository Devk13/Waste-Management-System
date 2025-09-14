# path: backend/app/api/routes.py
from __future__ import annotations
from fastapi import APIRouter

router = APIRouter()

# REQUIRED: /skips (always present)
from app.api import skips as skips_api  # type: ignore
router.include_router(skips_api.router)
print("[routes] mounted app.api.skips")

# OPTIONAL: include only if present; never crash app
_optional_modules = [
    ("app.api.driver",   "router"),   # legacy /driver endpoints (if you add them)
    ("app.api.dispatch", "router"),   # dispatch endpoints (if you add them)
    ("app.api.drivers",  "router"),   # the /drivers/me endpoint we added
]

for modpath, attr in _optional_modules:
    try:
        mod = __import__(modpath, fromlist=[attr])
        router.include_router(getattr(mod, attr))
        print(f"[routes] mounted {modpath}")
    except Exception as e:
        print(f"[routes] skipping {modpath}: {e}")
