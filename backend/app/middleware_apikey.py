# path: backend/app/middleware_apikey.py
from __future__ import annotations

import os
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Require `X-API-Key` for all `/driver/*` requests **only when** `ENV=prod`.
    - Key is taken from `DRIVER_API_KEY` (fallback to `ADMIN_API_KEY`).
    - `/driver/dev/ensure-skip` stays unprotected in dev; in prod the route returns 404 anyway.
    """

    def __init__(self, app):
        super().__init__(app)
        self.env = os.getenv("ENV", "dev").lower()
        self.required = os.getenv("DRIVER_API_KEY") or os.getenv("ADMIN_API_KEY") or ""

    async def dispatch(self, request, call_next):
        path = request.url.path

        # Protect /driver/* in prod (skip dev seed helper)
        if self.env == "prod" and path.startswith("/driver") and path != "/driver/dev/ensure-skip":
            key = request.headers.get("x-api-key") or ""
            if not self.required or key != self.required:
                # 401 keeps it simple for scripts; no WWW-Authenticate header
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        return await call_next(request)
