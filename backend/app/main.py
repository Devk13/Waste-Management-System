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


app = FastAPI(title="WMIS API")


# --- health (simple 200) ------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# --- meta/config for the frontend --------------------------------------------
@app.get("/meta/config")
def meta_config():
    """
    Small read-only config the frontend uses to render pickers and legends.
    """
    return {
        "driver_qr_base_url": settings.DRIVER_QR_BASE_URL,
        "skip": {
            "sizes": get_skip_size_presets(),
            "colors": SKIP_COLOR_SPEC,
        },
    }

# --- CORS ---------------------------------------------------------------
from app.core.config import settings, CORS_ORIGINS_LIST  # you already import these above

# Build a clean list from env (config splits the string already)
origins = [o for o in CORS_ORIGINS_LIST if o]

if not origins:
    # Fallback so we don't silently send no header (and avoid '*' with credentials)
    origins = [
        "https://waste-management-system-1-ie04.onrender.com",  # your frontend on Render
        # "http://localhost:5173",  # uncomment if you want local dev later
    ]
    print("WARN: CORS_ORIGINS was empty; using fallback:", origins, flush=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy import text

@app.get("/__debug/db")
async def debug_db():
    # Use the already-imported async engine
    dialect = engine.dialect.name  # e.g., "postgresql" or "sqlite"

    if dialect.startswith("postgres"):
        # List user-visible tables in the current schema (usually 'public')
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

# --- mount routes AFTER app is created ----------------------------------------
app.include_router(api_routes.router)
