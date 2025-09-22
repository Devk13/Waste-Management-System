# path: backend/app/main.py
from __future__ import annotations
import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from sqlalchemy import text
from urllib.parse import urlparse, parse_qs

from app.core.config import (
    settings,
    CORS_ORIGINS_LIST,
    SKIP_COLOR_SPEC,
    get_skip_size_presets,
)

# ✅ Single canonical engine
from app.core.deps import engine as db_engine

# Routers
from app.api.routes import api_router
from app.routers.admin import jobs as admin_jobs_router
from app.routers.driver import schedule_jobs as driver_schedule_router
from app.routers.admin import debug_settings as debug_settings_router

# Dev bootstrap models (optional)
from app.models.job import Base as JobsBase

# Optional: no-op fallback if middleware missing
try:
    from app.middleware_apikey import ApiKeyMiddleware
except Exception:
    class ApiKeyMiddleware:  # type: ignore
        def __init__(self, app, **_): self.app = app
        async def __call__(self, scope, receive, send): await self.app(scope, receive, send)

# Fallback admin_gate if deps import fails early
try:
    from app.core.deps import admin_gate
except Exception:
    async def admin_gate(x_api_key: str = Header(None, alias="X-API-Key")):
        from fastapi import HTTPException, status
        if not getattr(settings, "EXPOSE_ADMIN_ROUTES", False):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if x_api_key != getattr(settings, "ADMIN_API_KEY", ""):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")

log = logging.getLogger("uvicorn")

# ---- Single source of truth for DB URL (from active engine) ----
def _active_db_url() -> str:
    try:
        return str(db_engine.url)
    except Exception:
        return "unknown"

DB_URL = _active_db_url()

# ---- App ----
app = FastAPI(title="Waste Management System")

# ---- CORS (avoid '*' with credentials) ----
WILDCARD = (CORS_ORIGINS_LIST == ["*"]) or ("*" in CORS_ORIGINS_LIST)
ALLOW_CREDS = bool(getattr(settings, "CORS_ALLOW_CREDENTIALS", False)) and not WILDCARD
ALLOW_ORIGINS = ["*"] if WILDCARD else CORS_ORIGINS_LIST

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=ALLOW_CREDS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    ApiKeyMiddleware,
    protected_prefixes=("/driver",),
    allow_prefixes=("/__meta", "/__debug", "/docs", "/redoc", "/openapi.json", "/skips/__smoke"),
    hide_403=False,
)

# ---- Mount routers once ----
app.include_router(driver_schedule_router.router)
app.include_router(api_router)
app.include_router(admin_jobs_router.router)
app.include_router(debug_settings_router.router)

# --- Admin: Drivers & Vehicles ---------------------------------------------
try:
    from app.api.admin_drivers import router as admin_drivers_router
    app.include_router(admin_drivers_router)
except Exception as e:
    print(f"[main] WARN: couldn't mount admin_drivers: {type(e).__name__}: {e}", flush=True)

try:
    from app.api.admin_vehicles import router as admin_vehicles_router
    app.include_router(admin_vehicles_router)
except Exception as e:
    print(f"[main] WARN: couldn't mount admin_vehicles: {type(e).__name__}: {e}", flush=True)

# ---- Health / meta ----
@app.get("/__health")
async def health():
    try:
        async with db_engine.begin() as conn:
            await conn.execute(text("select 1"))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, f"db ping failed: {type(e).__name__}: {e}")

@app.get("/__meta/build")
def build_meta():
    return {"env": os.getenv("ENV", "dev"), "db_url": DB_URL}

@app.get("/meta/config")
def meta_config():
    return {
        "driver_qr_base_url": settings.DRIVER_QR_BASE_URL,
        "skip": {"sizes": get_skip_size_presets(), "colors": SKIP_COLOR_SPEC},
    }

@app.get("/__debug/engine")
def debug_engine():
    try:
        url = str(db_engine.url)
        dialect = db_engine.dialect.name
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    return {"dialect": dialect, "url": url}

# ---- Startup (dev-only create_all) ----
@app.on_event("startup")
async def _startup() -> None:
    log.info("[startup] WMIS main online")
    log.info("[startup] DB_URL = %s", DB_URL)
    log.info("[startup] CORS allow_origins=%s allow_credentials=%s", ALLOW_ORIGINS, ALLOW_CREDS)

    env = (os.getenv("ENV") or getattr(settings, "ENV", "dev")).lower()
    if env == "dev":
        try:
            from app.models.skip import Base as SkipBase
            from app.models.labels import Base as LabelsBase
            from app.models.driver import Base as DriverBase
            try:
                from app.models.models import Base as CoreBase
            except Exception:
                CoreBase = None  # type: ignore
            try:
                from app.models.vehicle import Base as VehicleBase
            except Exception:
                VehicleBase = None  # type: ignore

            groups = [("skips", SkipBase), ("labels", LabelsBase), ("driver", DriverBase), ("jobs", JobsBase)]
            if CoreBase is not None: groups.append(("core", CoreBase))
            if VehicleBase is not None: groups.append(("vehicles", VehicleBase))

            async with db_engine.begin() as conn:
                for name, base in groups:
                    try:
                        await conn.run_sync(base.metadata.create_all)
                        log.info("[bootstrap] ensured %s", name)
                    except Exception as e:
                        log.warning("[bootstrap] create_all(%s) failed: %s", name, e)
        except Exception as e:
            log.warning("[bootstrap] engine.begin() failed: %s", e)
    else:
        log.info("[bootstrap] skip create_all in non-dev")

    # enumerate mounted routes (debug)
    try:
        for r in app.routes:
            if isinstance(r, APIRoute):
                m = ",".join(sorted(r.methods or []))
                log.info("[ROUTE] %-10s %s", m, r.path)
    except Exception as exc:
        log.warning("Failed to enumerate routes: %s", exc)

# ---- DB helpers (use db_engine) ----
@app.get("/__debug/db")
async def debug_db():
    try:
        dialect = db_engine.dialect.name
        sql = text(
            "select table_name from information_schema.tables where table_schema = current_schema() order by table_name"
            if dialect.startswith("postgres") else
            "select name as table_name from sqlite_master where type='table' order by name"
        )
        async with db_engine.begin() as conn:
            rows = await conn.execute(sql)
            return {"dialect": dialect, "tables": [r[0] for r in rows.fetchall()]}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

@app.get("/__debug/db_url")
def debug_db_url():
    u = urlparse(DB_URL); nl = u.netloc
    if "@" in nl and ":" in nl.split("@", 1)[0]:
        user, host = nl.split("@", 1); user = user.split(":")[0] + ":***"; nl = user + "@" + host
    return {"scheme": u.scheme, "netloc": nl, "query": u.query}

# ---- Mounts inspector ----
@app.get("/__debug/mounts")
def __debug_mounts() -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for r in app.routes:
        if not isinstance(r, APIRoute):
            continue
        path = r.path or "/"
        seg = path.split("/", 2)[1] if "/" in path[1:] else ""
        key = "/" + seg if seg else "/"
        entry = seen.setdefault(key, {"prefix": key, "routes": 0, "examples": []})
        entry["routes"] += 1
        if len(entry["examples"]) < 3:
            entry["examples"].append({"path": path, "methods": sorted(list(r.methods or []))})
    expected = ["/driver", "/skips", "/__debug", "/__meta", "/wtn", "/admin"]
    return [{"prefix": k, **v, "expected": k in expected} for k, v in sorted(seen.items())]

@app.get("/__meta/ping")
def __meta_ping() -> Dict[str, Any]:
    return {"ok": True}

@app.get("/__debug/routes")
def __debug_routes() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            out.append({"path": r.path, "methods": sorted(list(r.methods or [])), "name": r.name})
    return out

# Admin-only: effective settings snapshot (unchanged; uses DB_URL above)
@app.get("/__debug/settings", dependencies=[Depends(admin_gate)])
def __debug_settings():
    def _mask(s: str | None) -> str:
        if not s: return ""
        return s[:2] + "…" + s[-2:] if len(s) > 6 else "***"

    wildcard = (CORS_ORIGINS_LIST == ["*"]) or ("*" in CORS_ORIGINS_LIST)
    allow_creds = bool(getattr(settings, "CORS_ALLOW_CREDENTIALS", False)) and not wildcard
    allow_origins = ["*"] if wildcard else CORS_ORIGINS_LIST

    u = urlparse(DB_URL); q = parse_qs(u.query)
    db_info = {
        "scheme": u.scheme,
        "host": u.hostname,
        "ssl": q.get("ssl", [""])[0] or q.get("sslmode", [""])[0] or "",
    }

    paths = {getattr(r, "path", "") for r in app.routes}
    routes_info = {
        "admin_jobs_mounted": any(p.startswith("/admin/jobs") for p in paths),
        "driver_schedule_mounted": "/driver/schedule" in paths and "/driver/schedule/{task_id}/done" in paths,
        "debug_routes": "/__debug/routes" in paths,
        "debug_mounts": "/__debug/mounts" in paths,
    }

    return {
        "env": getattr(settings, "ENV", "dev"),
        "debug": bool(getattr(settings, "DEBUG", False)),
        "expose_admin_routes": bool(getattr(settings, "EXPOSE_ADMIN_ROUTES", False)),
        "driver_qr_base_url": getattr(settings, "DRIVER_QR_BASE_URL", ""),
        "cors": {
            "origins_list": CORS_ORIGINS_LIST,
            "wildcard": wildcard,
            "allow_credentials_effective": allow_creds,
            "allow_origins_effective": allow_origins,
        },
        "keys": {
            "admin_api_key_masked": _mask(getattr(settings, "ADMIN_API_KEY", "")),
            "driver_api_key_masked": _mask(getattr(settings, "DRIVER_API_KEY", "")),
            "admin_api_key_set": bool(getattr(settings, "ADMIN_API_KEY", "")),
            "driver_api_key_set": bool(getattr(settings, "DRIVER_API_KEY", "")),
        },
        "db": db_info,
        "routes": routes_info,
    }

# Try to mount /skips; keep booting if it fails
try:
    from app.api.skips import router as skips_router
    app.include_router(skips_router, prefix="/skips")
except Exception as e:
    print(f"[main] WARN: couldn't mount app.api.skips: {type(e).__name__}: {e}", flush=True)
