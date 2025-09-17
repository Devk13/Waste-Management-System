from fastapi import APIRouter, Request
from typing import List, Dict

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
