# backend/app/middleware_apikey.py
from __future__ import annotations
from typing import Iterable, Tuple
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

def _norm(xs: Iterable[str] | None) -> Tuple[str, ...]:
    if not xs: return tuple()
    out = []
    for x in xs:
        if not x: continue
        out.append(x if x.startswith("/") else "/" + x)
    return tuple(sorted(set(out)))

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
        self.header = header_name
        self.env_var = env_var
        self.protected = _norm(protected_prefixes)
        self.allowed = _norm(allow_prefixes)
        self.hide = hide_as_404

    async def dispatch(self, request: Request, call_next) -> Response:
        # Only enforce in prod
        if (os.getenv("ENV") or "dev").lower() != "prod":
            return await call_next(request)

        path = request.url.path or "/"

        # public probes/docs always allowed
        if any(path.startswith(p) for p in self.allowed):
            return await call_next(request)

        # enforce only for protected prefixes
        if not any(path.startswith(p) for p in self.protected):
            return await call_next(request)

        key = request.headers.get(self.header)
        expected = os.getenv(self.env_var, "")
        if key and expected and key == expected:
            return await call_next(request)

        if self.hide:
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return JSONResponse({"detail": "Missing or invalid API key"}, status_code=401)
