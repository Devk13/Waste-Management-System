# path: backend/app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

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

app = FastAPI(title="WMIS API")

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

# ---------------------------------------------------------------------
# Create tables once at startup (quick bootstrap; Alembic later)
# ---------------------------------------------------------------------
@app.on_event("startup")
async def _bootstrap_db() -> None:
    # Only creates if missing; no-op if already present.
    async with engine.begin() as conn:
        await conn.run_sync(SkipBase.metadata.create_all)
        await conn.run_sync(LabelsBase.metadata.create_all)

# ---------------------------------------------------------------------
# Tiny DB check to verify connectivity/migrations (used during smoke tests)
# ---------------------------------------------------------------------
@app.get("/__debug/db")
async def debug_db():
    # Use the already-imported async engine
    dialect = engine.dialect.name  # e.g., "postgresql" or "sqlite"

    if dialect.startswith("postgres"):
        # List user-visible tables in current schema (usually 'public')
        sql = text("""
            select table_name
            from information_schema.tables
            where table_schema = current_schema()
            order by table_name
        """)
    else:
        # SQLite (local dev)
        sql = text("select name as table_name from sqlite_master where type='table' order by name")

    async with engine.begin() as conn:
        res = await conn.execute(sql)
        tables = [row[0] for row in res.fetchall()]

    return {"dialect": dialect, "tables": tables}

# ---------------------------------------------------------------------
# Mount all API routes AFTER app is created
# ---------------------------------------------------------------------
app.include_router(api_routes.router)
