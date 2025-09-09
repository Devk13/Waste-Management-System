# path: backend/app/api/routes.py

from fastapi import APIRouter

# Always required for labels
from app.api import skips as skips_api

# Optional: only if these modules exist in your project
try:
    from app.api import driver as driver_api
except Exception:
    driver_api = None  # pragma: no cover

try:
    from app.api import dispatch as dispatch_api
except Exception:
    dispatch_api = None  # pragma: no cover

try:
    from app.api import drivers as drivers_me_api  # /drivers/me
except Exception:
    drivers_me_api = None  # pragma: no cover


router = APIRouter()

# Required
router.include_router(skips_api.router)

# Optional
if driver_api:
    router.include_router(driver_api.router)
if dispatch_api:
    router.include_router(dispatch_api.router)
if drivers_me_api:
    router.include_router(drivers_me_api.router)
