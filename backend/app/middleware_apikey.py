# path: backend/app/middleware_apikey.py

from __future__ import annotations

import os
from typing import Iterable, Tuple, Set, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, PlainTextResponse

# Import your existing settings; keep a dev fallback.
try:
    from app.core.config import settings  # type: ignore[attr-defined]
except Exception:
    class _S:
        ENV = "dev"
        DRIVER_API_KEY = "driverapi"
        ADMIN_API_KEY = "super-temp-seed-key"
        SEED_API_KEY = ""
    settings = _S()  # type: ignore


def _prefix_match(path: str, prefixes: Iterable[str]) -> bool:
    if not prefixes:
        return False
    p = path if path.startswith("/") else f"/{path}"
    for pref in prefixes:
        if not pref:
            continue
        if not pref.startswith("/"):
            pref = "/" + pref
        if p == pref or p.startswith(pref if pref.endswith("/") else pref + "/"):
            return True
    return False


def _cors_headers(request: Request) -> dict:
    origin = request.headers.get("origin", "*")
    req_headers = request.headers.get("access-control-request-headers", "x-api-key, content-type")
    req_method = request.headers.get("access-control-request-method", "POST")
    return {
        "access-control-allow-origin": origin or "*",
        "access-control-allow-credentials": "true",
        "access-control-allow-methods": req_method or "*",
        "access-control-allow-headers": req_headers or "x-api-key, content-type",
        "vary": "Origin",
    }


def _split_keys(raw: Optional[str]) -> Set[str]:
    if not raw:
        return set()
    parts = [p.strip() for p in str(raw).split(",")]
    return {p for p in parts if p}


def _get_setting(obj, *names: str) -> Optional[str]:
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if isinstance(v, str) and v.strip():
                return v
    return None


def _build_valid_keys() -> Set[str]:
    candidates: Set[str] = set()
    candidates |= _split_keys(_get_setting(settings, "DRIVER_API_KEY", "driver_api_key"))
    candidates |= _split_keys(_get_setting(settings, "ADMIN_API_KEY", "admin_api_key"))
    candidates |= _split_keys(_get_setting(settings, "SEED_API_KEY", "seed_api_key"))
    candidates |= _split_keys(os.getenv("DRIVER_API_KEY"))
    candidates |= _split_keys(os.getenv("ADMIN_API_KEY"))
    candidates |= _split_keys(os.getenv("SEED_API_KEY"))
    return {c.strip() for c in candidates if c and c.strip()}


def _fingerprint(k: str) -> str:
    return f"{len(k)}:{k[:2]}…{k[-2:]}" if len(k) > 4 else f"{len(k)}:{k or '<empty>'}"


def _get_supplied_key(request: Request, header_name: str) -> str:
    key = (request.headers.get(header_name) or "").strip()
    if key:
        return key
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return ""


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        protected_prefixes: Iterable[str] = ("/driver",),
        allow_prefixes: Iterable[str] = (
            "/meta",
            "/_meta",
            "/_debug",
            "/_health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/skips/__smoke",
        ),
        header_name: str = "x-api-key",
        hide_403: bool = False,
    ) -> None:
        super().__init__(app)
        self.protected: Tuple[str, ...] = tuple(protected_prefixes or ())
        self.allowed: Tuple[str, ...] = tuple(allow_prefixes or ())
        self.header_name = header_name
        self.hide_403 = hide_403
        self.valid_keys: Set[str] = _build_valid_keys()

        if str(getattr(settings, "ENV", "dev")).lower() in {"dev", "local"}:
            fps = ", ".join(sorted(_fingerprint(k) for k in self.valid_keys)) or "<none>"
            print(f"[auth] Loaded {len(self.valid_keys)} API key(s): {fps}")

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        if request.method == "HEAD":
            return await call_next(request)
        if request.method == "OPTIONS":
            return PlainTextResponse("", status_code=204, headers=_cors_headers(request))

        if _prefix_match(path, self.allowed):
            resp = await call_next(request)
            for k, v in _cors_headers(request).items():
                resp.headers.setdefault(k, v)
            return resp

        if _prefix_match(path, self.protected):
            supplied = _get_supplied_key(request, self.header_name)
            if not supplied:
                return self._deny(missing=True)
            if supplied not in self.valid_keys:
                if str(getattr(settings, "ENV", "dev")).lower() in {"dev", "local"}:
                    print(f"[auth] Invalid key len={len(supplied)} value='{supplied}' vs loaded={len(self.valid_keys)}")
                return self._deny(missing=False)
            resp = await call_next(request)
            for k, v in _cors_headers(request).items():
                resp.headers.setdefault(k, v)
            return resp

        resp = await call_next(request)
        for k, v in _cors_headers(request).items():
            resp.headers.setdefault(k, v)
        return resp

    def _deny(self, *, missing: bool) -> Response:
        if self.hide_403:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        return JSONResponse(
            {"detail": "Missing API key" if missing else "Invalid API key"},
            status_code=401 if missing else 403,
            headers={"access-control-allow-origin": "*"},
        )
