# path: backend/app/main.py
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import (
    SKIP_COLOR_SPEC,
    get_skip_size_presets,
)
from app.core.config import settings, CORS_ORIGINS_LIST
from app.core.config import settings          # <— same import
from app.db import engine
from app.api import routes as api_routes      # <— you already have this

app = FastAPI(title="WMIS API")

@app.get("/meta/config")
def meta_config():
    """
    Small read-only shape for the frontend so it can render pickers and legends.
    """
    return {
        "driver_qr_base_url": settings.DRIVER_QR_BASE_URL,
        "skip": {
            "sizes": get_skip_size_presets(),
            "colors": SKIP_COLOR_SPEC,
        },
    }

# CORS
ORIGINS = CORS_ORIGINS_LIST or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- optional tiny DB check (keep if you like) ----------------------------
@app.get("/__debug/db")
async def debug_db():
    async with engine.begin() as conn:
        rows = (await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))).fetchall()
    return {"tables": [r[0] for r in rows]}

# --- mount routes AFTER app is created -----------------------------------
app.include_router(api_routes.router)
