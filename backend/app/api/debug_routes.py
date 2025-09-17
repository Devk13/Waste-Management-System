from __future__ import annotations
from fastapi import APIRouter, Request
from typing import List, Dict, Any
from fastapi.routing import APIRoute

router = APIRouter(prefix="/__debug", tags=["__debug"])

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
    items: List[Dict[str, Any]] = []
    for r in request.app.routes:
        if isinstance(r, APIRoute):
            items.append({
                "path": r.path,
                "methods": sorted(list(r.methods or [])),
                "name": r.name,
            })
    return items
