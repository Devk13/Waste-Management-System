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

# in backend/app/main.py
from sqlalchemy import text

@app.get("/__debug/db")
async def debug_db():
    async with engine.begin() as conn:
        # Pick a table listing query appropriate to the engine
        if conn.engine.name.startswith("postgresql"):
            q = text("select tablename from pg_catalog.pg_tables "
                     "where schemaname not in ('pg_catalog','information_schema') "
                     "order by tablename")
        else:
            q = text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        rows = (await conn.execute(q)).fetchall()
        return {"tables": [r[0] for r in rows]}

# --- mount routes AFTER app is created ----------------------------------------
app.include_router(api_routes.router)
