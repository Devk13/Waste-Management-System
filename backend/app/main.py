# path: backend/app/main.py
from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import asyncio
import logging
# create tables for these model groups
from app.models.skip import Base as SkipBase
from app.models.labels import Base as LabelsBase
from app.models.driver import Base as DriverBase
from sqlalchemy.exc import SQLAlchemyError  # optional, we’ll still catch Exception
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.middleware_apikey import ApiKeyMiddleware
from app.api.routes import api_router

from app.core.config import (
    settings,
    CORS_ORIGINS_LIST,
    SKIP_COLOR_SPEC,
    get_skip_size_presets,
)
from app.db import engine
from app.api import routes as api_routes
from app.models.skip import Base as SkipBase
from app.models.labels import Base as LabelsBase
from urllib.parse import urlparse
from app.db import engine, DB_URL

app = FastAPI(title="WMIS API")
app.include_router(api_router)

try:
    from app.core.config import settings  # optional
except Exception:
    settings = None  # type: ignore

log = logging.getLogger("uvicorn")
app = FastAPI(title="Waste Management System")
# ---------------------------------------------------------------------
# CORS (single block)
# ---------------------------------------------------------------------
ORIGINS = CORS_ORIGINS_LIST or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ApiKeyMiddleware)

# ---------------------------------------------------------------------
# Meta config for the frontend (skip sizes + color legend + driver QR base)
# ---------------------------------------------------------------------
@app.get("/meta/config")
def meta_config():
    """
    Small read-only shape for the PWA so it can render pickers and legends.
    """
    return {
        "driver_qr_base_url": settings.DRIVER_QR_BASE_URL,
        "skip": {
            "sizes": get_skip_size_presets(),  # {"sizes_m3":[...], "wheelie_l":[...], "rolloff_yd":[...]}
            "colors": SKIP_COLOR_SPEC,         # {"white":{...}, "grey":{...}, ...}
        },
    }

def _is_dev() -> bool:
    """True when ENV=dev (env var or settings), else False."""
    env = os.getenv("ENV") or (getattr(settings, "ENV", None) if settings else None) or "dev"
    return str(env).lower() == "dev"

# --- create tables once at startup (quick bootstrap; replace with Alembic later) ---

@app.on_event("startup")
async def _startup() -> None:
    # 1) Show the DB URL & mounted routes (super helpful on Render/local)
    log.info("[db] Using DB_URL = %r", DB_URL)
    try:
        for r in app.routes:
            p = getattr(r, "path", "")
            m = ",".join(sorted(getattr(r, "methods", []) or []))
            if p:
                log.info("[ROUTE] %-10s %s", m, p)
    except Exception as exc:
        log.warning("Failed to enumerate routes: %s", exc)

    # 2) DEV ONLY: quick local bootstrap (Alembic owns prod)
    if not _is_dev():
        log.info("[bootstrap] skip create_all in non-dev")
        return

    try:
        from app.models.skip import Base as SkipBase
        from app.models.labels import Base as LabelsBase
        from app.models.driver import Base as DriverBase

        groups = [
            ("skips", SkipBase),
            ("labels", LabelsBase),
            ("driver", DriverBase),
        ]
        async with engine.begin() as conn:
            for name, base in groups:
                try:
                    await conn.run_sync(base.metadata.create_all)
                    log.info("[bootstrap] ensured tables for %s", name)
                except Exception as e:
                    log.warning("[bootstrap] WARN: create_all(%s) failed: %s", name, e)
    except Exception as e:
        log.warning("[bootstrap] WARN: engine.begin() failed: %s", e)

# ---------------------------------------------------------------------
# Tiny DB check to verify connectivity/migrations (used during smoke tests)
# ---------------------------------------------------------------------
@app.get("/__health", tags=["__debug"])
async def health():
    """DB connectivity check used by smoke tests and Render health."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("select 1"))
        return {"ok": True}
    except Exception as e:
        # single-line reason for logs/clients
        raise HTTPException(status_code=500, detail=f"db ping failed: {type(e).__name__}: {e}")

@app.get("/__debug/db")
async def debug_db():
    try:
        dialect = engine.dialect.name  # e.g. "postgresql+asyncpg" or "sqlite"
        if dialect.startswith("postgres"):
            sql = text("""
                select table_name
                from information_schema.tables
                where table_schema = current_schema()
                order by table_name
            """)
        else:
            sql = text("select name as table_name from sqlite_master where type='table' order by name")
        async with engine.begin() as conn:
            res = await conn.execute(sql)
            tables = [row[0] for row in res.fetchall()]
        return {"dialect": dialect, "tables": tables}
    except Exception as e:
        # return the raw reason instead of a generic 500
        return JSONResponse(
            status_code=500,
            content={"error": f"{type(e).__name__}: {e}"}
        )


@app.get("/__debug/db_url")
def debug_db_url():
    u = urlparse(DB_URL if "DB_URL" in globals() else settings.DATABASE_URL)
    # mask password
    netloc = u.netloc
    if "@" in netloc and ":" in netloc.split("@", 1)[0]:
        user, host = netloc.split("@", 1)
        user = user.split(":")[0] + ":***"
        netloc = user + "@" + host
    return {
        "scheme": u.scheme,          # should be postgresql+asyncpg
        "netloc": netloc,
        "query": u.query,            # if present, should contain ssl=true (NOT sslmode=...)
    }


# --- TEMP: force-mount admin skips demo so it appears in /docs right away
try:
    from app.api.skips_demo import router as admin_skips_router
    app.include_router(admin_skips_router, tags=["admin-skips"])
    print("[main] mounted admin_skips_router", flush=True)
except Exception as e:
    print(f"[main] couldn't mount admin_skips_router: {e}", flush=True)

# --- Ensure /skips is mounted even if the helper or tag logic differs
try:
    # if your module exposes `router`
    from app.api.skips import router as skips_router
except Exception:
    # some projects name it `skips_api`
    from app.api.skips import skips_api as skips_router
app.include_router(skips_router, prefix="/skips", tags=["skips"])
