from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Request
from fastapi.routing import APIRoute

router = APIRouter(tags=["__debug"])

@router.get("/__debug/routes")
def list_routes(request: Request) -> List[Dict[str, Any]]:
    # why: enumerate live mounted routes
    out: List[Dict[str, Any]] = []
    for r in request.app.routes:
        if isinstance(r, APIRoute):
            out.append({"path": r.path, "methods": sorted(list(r.methods or [])), "name": r.name})
    return out

@router.get("/__debug/mounts")
def list_mounts() -> List[Dict[str, Any]]:
    # why: show results from dynamic mounting (if available)
    try:
        from app.api import routes as routes_mod
        return getattr(routes_mod, "__mount_report__", [])
    except Exception as e:
        return [{"ok": False, "error": f"{type(e).__name__}: {e}"}]
