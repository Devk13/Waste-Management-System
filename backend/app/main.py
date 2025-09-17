# backend/app/main.py
from __future__ import annotations
import os
import logging
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.api.routes import api_router
from app.db import DB_URL, engine
from app.core.config import settings, CORS_ORIGINS_LIST, SKIP_COLOR_SPEC, get_skip_size_presets
from app.middleware_apikey import ApiKeyMiddleware

log = logging.getLogger("uvicorn")

# One app only
app = FastAPI(title="Waste Management System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS_LIST or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API-key: protect driver*, allow public probes/docs
app.add_middleware(
    ApiKeyMiddleware,
    protected_prefixes=("/driver",),
    allow_prefixes=("/__meta", "/__debug", "/docs", "/redoc", "/openapi.json", "/skips/__smoke"),
    hide_as_404=False,  # show 401 if missing key on protected routes
)

# Small meta for UI pickers/legends
@app.get("/meta/config")
def meta_config():
    return {
        "driver_qr_base_url": settings.DRIVER_QR_BASE_URL,
        "skip": {"sizes": get_skip_size_presets(), "colors": SKIP_COLOR_SPEC},
    }

@app.on_event("startup")
async def _startup() -> None:
    print("[startup] WMIS main online", flush=True)
    print(f"[startup] DB_URL = {DB_URL}", flush=True)
    for r in app.routes:
        p = getattr(r, "path", "")
        if p:
            log.info("[ROUTE] %s", p)

# Normal API bundle
app.include_router(api_router)

# Health + DB helpers
@app.get("/__health", tags=["__debug"])
async def health():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("select 1"))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"db ping failed: {type(e).__name__}: {e}")

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
    u = urlparse(DB_URL)
    nl = u.netloc
    if "@" in nl and ":" in nl.split("@", 1)[0]:
        user, host = nl.split("@", 1)
        user = user.split(":")[0] + ":***"
        nl = user + "@" + host
    return {"scheme": u.scheme, "netloc": nl, "query": u.query}

# Guaranteed probes (public)
@app.get("/__meta/ping")
def __meta_ping() -> Dict[str, Any]:
    return {"ok": True}

@app.get("/__meta/build")
def __meta_build() -> Dict[str, Any]:
    return {"env": os.getenv("ENV", "dev"), "sha": os.getenv("RENDER_GIT_COMMIT", os.getenv("GIT_SHA", "")), "app_dir": "backend"}

@app.get("/__debug/routes")
def __debug_routes() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            out.append({"path": r.path, "methods": sorted(list(r.methods or [])), "name": r.name})
    return out

@app.get("/skips/__smoke")
async def __skips_smoke() -> Dict[str, Any]:
    res: Dict[str, Any] = {"ok": True}
    try:
        async with engine.begin() as conn:  
            async def count(tbl: str) -> int:
                try:
                    rows = await conn.execute(text(f"select count(*) from {tbl}"))
                    return int(list(rows)[0][0])
                except Exception:
                    return -1
            res.update({
                "skips": await count("skips"),
                "placements": await count("skip_placements"),
                "movements": await count("movements"),
                "weights": await count("weights"),
                "transfers": await count("transfers"),
                "wtns": await count("wtns"),
            })
    except Exception as e:
        res["ok"] = False
        res["error"] = f"{type(e).__name__}: {e}"
    return res

# Ensure /skips mounts even if dynamic include hiccups
try:
    from app.api.skips import router as skips_router
    app.include_router(skips_router, prefix="/skips", tags=["skips"])  
except Exception as e:
    print(f"[main] couldn't mount app.api.skips: {e}", flush=True)
