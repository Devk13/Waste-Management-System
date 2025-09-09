# ─────────────────────────────────────────────────────────────────────────────
# path: backend/app/api/routes.py  (REPLACE or MERGE)
# Ensures the /skips endpoints are registered.
# ─────────────────────────────────────────────────────────────────────────────
from fastapi import APIRouter

# Keep your other routers if you have them
try:
    from app.api import driver as driver_api  # optional
except Exception:  # pragma: no cover
    driver_api = None

try:
    from app.api import dispatch as dispatch_api  # optional
except Exception:  # pragma: no cover
    dispatch_api = None

try:
    from app.api import drivers as drivers_me_api  # optional (/drivers/me)
except Exception:  # pragma: no cover
    drivers_me_api = None

from app.api import skips as skips_api  # <-- REQUIRED for /skips

router = APIRouter()

# Required
router.include_router(skips_api.router)

# Optional (only if present in your project)
if driver_api:
    router.include_router(driver_api.router)
if dispatch_api:
    router.include_router(dispatch_api.router)
if drivers_me_api:
    router.include_router(drivers_me_api.router)
