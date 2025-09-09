# path: backend/app/api/routes.py
from fastapi import APIRouter

from app.api import driver as driver_api
from app.api import dispatch as dispatch_api
from app.api import drivers as drivers_api  # /drivers/me
from app.api import skips as skips_api      # /skips + labels

router = APIRouter()

router.include_router(driver_api.router)
router.include_router(dispatch_api.router)
router.include_router(drivers_api.router)
router.include_router(skips_api.router)
