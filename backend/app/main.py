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
from app.db import DB_URL  # keep DB_URL for debug endpoint
from app.core.deps import engine  # single engine source
from app.api.routes import api_router
from app.routers.admin import jobs as admin_jobs_router
from app.routers.driver import schedule_jobs as driver_schedule_router
from app.models.job import Base as JobsBase  # ensure jobs table in dev bootstrap
from app.routers.admin import debug_settings as debug_settings_router

# optional: no-op fallback if middleware file is missing
try:
    from app.middleware_apikey import ApiKeyMiddleware
except Exception:
    class ApiKeyMiddleware:  # type: ignore
        def __init__(self, app, **_): self.app = app
        async def __call__(self, scope, receive, send): await self.app(scope, receive, send)

try:
    from app.core.deps import admin_gate
except Exception:
    # Why: keep /__debug/settings admin-only even if deps import fails.
    async def admin_gate(x_api_key: str = Header(None, alias="X-API-Key")):
        from fastapi import HTTPException, status
        from app.core.config import settings
        if not getattr(settings, "EXPOSE_ADMIN_ROUTES", False):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if x_api_key != getattr(settings, "ADMIN_API_KEY", ""):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")

log = logging.getLogger("uvicorn")

# 1) app
app = FastAPI(title="Waste Management System")

# 2) middleware
# WHY: Browsers reject '*' with credentials; auto-disable credentials if wildcard is used.
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

# 3) routes (mount once)
app.include_router(api_router)
app.include_router(admin_jobs_router.router)
app.include_router(driver_schedule_router.router)
app.include_router(debug_settings_router.router)

# 4) health/meta
@app.get("/__health")
async def health():
    try:
        async with engine.begin() as conn:
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

# 5) startup
@app.on_event("startup")
async def _startup() -> None:
    print("[startup] WMIS main online", flush=True)
    print(f"[startup] DB_URL = {DB_URL}", flush=True)
    print(f"[startup] CORS allow_origins={ALLOW_ORIGINS} allow_credentials={ALLOW_CREDS}", flush=True)

    # DEV bootstrap: create tables if running locally (ENV=dev)
    env = (os.getenv("ENV") or getattr(settings, "ENV", "dev")).lower()
    if env == "dev":
        try:
            from app.models.skip import Base as SkipBase
            from app.models.labels import Base as LabelsBase
            from app.models.driver import Base as DriverBase
            try:
                from app.models.models import Base as CoreBase  # movements, weights, transfers, wtns
            except Exception:
                CoreBase = None  # type: ignore
            try:
                from app.models.vehicle import Base as VehicleBase
            except Exception:
                VehicleBase = None  # type: ignore

            # include jobs base here (WHY: ensure jobs table exists for local/dev)
            groups = [("skips", SkipBase), ("labels", LabelsBase), ("driver", DriverBase), ("jobs", JobsBase)]
            if CoreBase is not None:
                groups.append(("core", CoreBase))
            if VehicleBase is not None:
                groups.append(("vehicles", VehicleBase))

            async with engine.begin() as conn:
                for name, base in groups:
                    try:
                        await conn.run_sync(base.metadata.create_all)
                        logging.getLogger("uvicorn").info("[bootstrap] ensured %s", name)
                    except Exception as e:
                        logging.getLogger("uvicorn").warning("[bootstrap] create_all(%s) failed: %s", name, e)
        except Exception as e:
            logging.getLogger("uvicorn").warning("[bootstrap] engine.begin() failed: %s", e)
    else:
        logging.getLogger("uvicorn").info("[bootstrap] skip create_all in non-dev")

    # enumerate routes
    try:
        for r in app.routes:
            if isinstance(r, APIRoute):
                m = ",".join(sorted(r.methods or []))
                logging.getLogger("uvicorn").info("[ROUTE] %-10s %s", m, r.path)
    except Exception as exc:
        logging.getLogger("uvicorn").warning("Failed to enumerate routes: %s", exc)

# 6) debug helpers
@app.get("/__debug/db")
async def debug_db():
    try:
        dialect = engine.dialect.name
        sql = text(
            "select table_name from information_schema.tables where table_schema = current_schema() order by table_name"
            if dialect.startswith("postgres") else
            "select name as table_name from sqlite_master where type='table' order by name"
        )
        async with engine.begin() as conn:
            rows = await conn.execute(sql)
            return {"dialect": dialect, "tables": [r[0] for r in rows.fetchall()]}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}

@app.get("/__debug/db_url")
def debug_db_url():
    from urllib.parse import urlparse
    u = urlparse(DB_URL); nl = u.netloc
    if "@" in nl and ":" in nl.split("@", 1)[0]:
        user, host = nl.split("@", 1); user = user.split(":")[0] + ":***"; nl = user + "@" + host
    return {"scheme": u.scheme, "netloc": nl, "query": u.query}

# --- mounts inspector (pure runtime) -----------------------------------
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

@app.get("/__debug/settings", dependencies=[Depends(admin_gate)])
def __debug_settings():
    """
    Admin-only: effective server settings (CORS, routes presence, env flags, masked keys, DB driver).
    """
    from app.core.config import settings, CORS_ORIGINS_LIST
    from app.db import DB_URL

    def _mask(s: str | None) -> str:
        if not s: return ""
        return s[:2] + "…" + s[-2:] if len(s) > 6 else "***"

    # CORS effective values (mirror your runtime logic)
    wildcard = (CORS_ORIGINS_LIST == ["*"]) or ("*" in CORS_ORIGINS_LIST)
    allow_creds = bool(getattr(settings, "CORS_ALLOW_CREDENTIALS", False)) and not wildcard
    allow_origins = ["*"] if wildcard else CORS_ORIGINS_LIST

    # DB summary
    u = urlparse(DB_URL)
    q = parse_qs(u.query)
    db_info = {
        "scheme": u.scheme,
        "host": u.hostname,
        "ssl": q.get("ssl", [""])[0] or q.get("sslmode", [""])[0] or "",
    }

    # Mounted route checks
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

# Try to mount /skips router; if it still has bad imports we keep booting
try:
    from app.api.skips import router as skips_router
    app.include_router(skips_router, prefix="/skips", tags=["skips"])
except Exception as e:
    print(f"[main] WARN: couldn't mount app.api.skips: {type(e).__name__}: {e}", flush=True)
