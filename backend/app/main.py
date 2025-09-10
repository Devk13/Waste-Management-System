# path: backend/app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

# Make sure these import the models but don’t execute app logic
from app.models.skip import Base as SkipBase
from app.models.labels import Base as LabelsBase
from app.db import engine

app = FastAPI(title="WMIS API")

# CORS
try:
    from app.core.config import settings  # type: ignore
    ORIGINS = [o.strip() for o in settings.CORS_ORIGINS.split(";") if o.strip()]
except Exception:  # pragma: no cover
    ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB bootstrap on startup (dev convenience)
@app.on_event("startup")
async def _bootstrap_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SkipBase.metadata.create_all)
        await conn.run_sync(LabelsBase.metadata.create_all)

# optional debug
@app.get("/__debug/db")
async def debug_db():
    async with engine.begin() as conn:
        rows = (await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))).fetchall()
        return {"tables": [r[0] for r in rows]}

# Include routers AFTER app exists
try:
    from app.api.routes import router as api_router
    app.include_router(api_router)
except Exception:
    # fall back to individual routers if you prefer
    from app.api.skips import router as skips_router
    app.include_router(skips_router)
