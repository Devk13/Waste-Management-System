# path: backend/app/main.py
from __future__ import annotations
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, CORS_ORIGINS_LIST, SKIP_COLOR_SPEC, get_skip_size_presets
from app.db import DB_URL, engine
from app.api.routes import api_router
from typing import Any, Dict, List
from fastapi.routing import APIRoute
from sqlalchemy import text

# optional: no-op fallback if middleware file is missing
try:
    from app.middleware_apikey import ApiKeyMiddleware
except Exception:
    class ApiKeyMiddleware:  # type: ignore
        def __init__(self, app, **_): self.app = app
        async def __call__(self, scope, receive, send): await self.app(scope, receive, send)

log = logging.getLogger("uvicorn")

# 1) create app first
app = FastAPI(title="Waste Management System")

# 2) middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # dev only; tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    ApiKeyMiddleware,
    protected_prefixes=("/driver",),
    allow_prefixes=("/__meta", "/__debug", "/docs", "/redoc", "/openapi.json", "/skips/__smoke"),
    hide_403=False,
)

# 3) include routes AFTER app exists
app.include_router(api_router)

# 4) tiny health + debug
@app.get("/__health")
async def health():
    try:
        async with engine.begin() as conn:
            await conn.execute("select 1")
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

@app.on_event("startup")
async def _startup() -> None:
    print("[startup] WMIS main online", flush=True)
    print(f"[startup] DB_URL = {DB_URL}", flush=True)

    # include routers (kept lazy so a bad import doesn't crash boot)
    try:
        from app.api.routes import api_router
        app.include_router(api_router)
        print("[startup] included api_router", flush=True)
    except Exception as e:
        print(f"[startup] WARN: couldn't include api_router: {type(e).__name__}: {e}", flush=True)

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
                from app.models.vehicle import Base as VehicleBase  # new
            except Exception:
                VehicleBase = None  # type: ignore

            groups = [("skips", SkipBase), ("labels", LabelsBase), ("driver", DriverBase)]
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

# Health + DB helpers (unchanged)
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

# --- new: guaranteed mounts inspector (no imports needed) --------------
@app.get("/__debug/mounts")
def __debug_mounts() -> List[Dict[str, Any]]:
    """
    Pure runtime view of what is actually mounted.
    Groups routes by first path segment and shows a sample.
    """
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
    # include quick booleans for expected groups
    expected = ["/driver", "/skips", "/__debug", "/__meta", "/wtn"]
    return [{"prefix": k, **v, "expected": k in expected} for k, v in sorted(seen.items())]

# --- existing probes you already added (keep) --------------------------
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
        res["ok"] = False; res["error"] = f"{type(e).__name__}: {e}"
    return res

# Try to mount /skips router; if it still has bad imports we keep booting
try:
    from app.api.skips import router as skips_router
    app.include_router(skips_router, prefix="/skips", tags=["skips"])
except Exception as e:
    print(f"[main] WARN: couldn't mount app.api.skips: {type(e).__name__}: {e}", flush=True)
