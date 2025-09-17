from __future__ import annotations
from fastapi import APIRouter, Request
from typing import List, Dict, Any
from fastapi.routing import APIRoute

router = APIRouter(tags=["__debug"])

@router.get("/routes", summary="List mounted routes")
async def list_routes(request: Request) -> List[Dict[str, str]]:
    # Why: fast verification of which routers actually mounted
    out: List[Dict[str, str]] = []
    for r in request.app.routes:
        path = getattr(r, "path", "")
        if not path:
            continue
        methods = sorted(getattr(r, "methods", []) or [])
        name = getattr(r, "name", "")
        out.append({"path": path, "methods": ",".join(methods), "name": name})
    out.sort(key=lambda x: (x["path"], x["methods"]))
    return out

@router.get("/__debug/routes")
def list_routes(request: Request) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in request.app.routes:
        if isinstance(r, APIRoute):
            out.append({"path": r.path, "methods": sorted(list(r.methods or [])), "name": r.name})
    return out

@router.get("/__debug/mounts")
def list_mounts() -> List[Dict[str, Any]]:
    try:
        from app.api import routes as routes_mod
        return getattr(routes_mod, "__mount_report__", [])
    except Exception as e:
        return [{"ok": False, "error": f"{type(e).__name__}: {e}"}]
