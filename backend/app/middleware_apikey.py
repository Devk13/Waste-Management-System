# ======================================================================
# file: backend/app/middleware_apikey.py
# Purpose: Protect only selected prefixes (default: /driver) in ENV=prod.
#          Allow public prefixes so probes/docs aren’t hidden as 404.
# ======================================================================
from __future__ import annotations
from typing import Iterable, Tuple
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

def _norm_prefixes(xs: Iterable[str] | None) -> Tuple[str, ...]:
    if not xs:
        return tuple()
    norm = []
    for x in xs:
        if not x:
            continue
        norm.append(x if x.startswith("/") else "/" + x)
    return tuple(sorted(set(norm)))

class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        header_name: str = "X-API-Key",
        env_var: str = "DRIVER_API_KEY",
        protected_prefixes: Iterable[str] = ("/driver",),
        allow_prefixes: Iterable[str] = ("/__meta", "/__debug", "/docs", "/redoc", "/openapi.json", "/skips/__smoke"),
        hide_as_404: bool = False,
    ) -> None:
        super().__init__(app)
        self.header_name = header_name
        self.env_var = env_var
        self.protected = _norm_prefixes(protected_prefixes)
        self.allow = _norm_prefixes(allow_prefixes)
        self.hide_as_404 = hide_as_404

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only enforce in prod; skip entirely in dev/test
        env = (os.getenv("ENV") or "dev").lower()
        if env != "prod":
            return await call_next(request)

        path = request.url.path or "/"

        # public prefixes are always allowed
        for p in self.allow:
            if path.startswith(p):
                return await call_next(request)

        # enforce only when path starts with any protected prefix
        enforce = any(path.startswith(p) for p in self.protected)
        if not enforce:
            return await call_next(request)

        key = request.headers.get(self.header_name)
        expected = os.getenv(self.env_var, "")
        if key and expected and key == expected:
            return await call_next(request)

        if self.hide_as_404:
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return JSONResponse({"detail": "Missing or invalid API key"}, status_code=401)
