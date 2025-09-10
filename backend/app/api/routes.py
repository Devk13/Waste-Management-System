# path: backend/app/api/routes.py
from __future__ import annotations
from fastapi import APIRouter

router = APIRouter()

# REQUIRED: /skips (this one should always exist)
from app.api import skips as skips_api  # type: ignore
router.include_router(skips_api.router)

# OPTIONAL: include these only if present
_optional_modules = [
    ("app.api.driver", "router"),     # your legacy /driver endpoints (if any)
    ("app.api.dispatch", "router"),   # dispatch endpoints (if any)
    ("app.api.drivers", "router"),    # the /drivers/me endpoint we added
]

for modpath, attr in _optional_modules:
    try:
        mod = __import__(modpath, fromlist=[attr])
        router.include_router(getattr(mod, attr))
    except Exception:
        # Silently skip when module isn't present in this project
        continue
