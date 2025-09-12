# path: backend/app/api/routes.py
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

# REQUIRED: /skips (always present)
from app.api import skips as skips_api  # type: ignore
router.include_router(skips_api.router)

# OPTIONAL: include these only if present
_optional_modules = [
    ("app.api.driver",   "router"),   # legacy /driver endpoints (if any)
    ("app.api.dispatch", "router"),   # dispatch endpoints (if any)
    ("app.api.drivers",  "router"),   # /drivers/me endpoint
    ("app.api.dev",      "router"),   # any temporary dev routes (optional)
]

for modpath, attr in _optional_modules:
    try:
        mod = __import__(modpath, fromlist=[attr])
        router.include_router(getattr(mod, attr))
        # print(f"[routes] mounted {modpath}")  # optional debug
    except Exception:
        # Silently skip when module isn't present in this project
        # print(f"[routes] skipping {modpath}: not present")  # optional debug
        continue
