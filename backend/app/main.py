# path: backend/app/main.py
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings  # for CORS
from app.db import engine

app = FastAPI(title="WMIS API")

# CORS
ORIGINS = [o.strip() for o in settings.CORS_ORIGINS.split(";") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# optional: tiny DB check
@app.get("/__debug/db")
async def debug_db():
    async with engine.begin() as conn:
        rows = (await conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))).fetchall()
    return {"tables": [r[0] for r in rows]}

# 👉 Mount all API routes (do this AFTER app is created)
from app.api import routes as api_routes  # noqa: E402
app.include_router(api_routes.router)
