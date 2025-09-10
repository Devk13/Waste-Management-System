# path: backend/app/main.py
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# use both Bases so both sets of tables get created
from app.models.skip import Base as SkipBase
from app.models.labels import Base as LabelsBase

# NEW: imports for DB bootstrap
from sqlalchemy import text
from app.db import engine
# If your models define separate Base objects, import both:
from app.models.labels import Base as LabelsBase

# CORS origins (existing code)
try:
    from app.core.config import settings  # type: ignore
    ORIGINS = [o.strip() for o in settings.CORS_ORIGINS.split(";") if o.strip()]
except Exception:  # pragma: no cover
    ORIGINS = ["*"]

app = FastAPI(title="WMIS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# DB bootstrap on startup (DEV/MVP convenience; safe to keep in dev)
# ─────────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def _bootstrap_db() -> None:
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(SkipBase.metadata.create_all)
        await conn.run_sync(LabelsBase.metadata.create_all)

# Small debug helper to verify tables exist
@app.get("/__debug/db")
async def debug_db():
    async with engine.begin() as conn:
        rows = (await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))).fetchall()
        return {"tables": [r[0] for r in rows]}

# ─────────────────────────────────────────────────────────────────────────────
# Include your routers (keep your existing includes)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from app.api.skips import router as skips_router
    app.include_router(skips_router)
except Exception:
    pass

# (…any other routers you include…)
