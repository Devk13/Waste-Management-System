from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.models.driver import WasteTransferNote

router = APIRouter(tags=["__debug"])

IS_PROD = str(getattr(settings, "ENV", "dev")).lower() == "prod"
ADMIN_KEY = str(getattr(settings, "ADMIN_API_KEY", ""))

def admin_gate(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not IS_PROD:
        return
    if not ADMIN_KEY or x_api_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin key required")

@router.get("/__debug/wtns", dependencies=[Depends(admin_gate)])
async def list_recent_wtns(limit: int = 10, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    stmt = select(WasteTransferNote).order_by(desc(WasteTransferNote.created_at)).limit(max(1, min(limit, 50)))
    res = await db.execute(stmt)
    rows: List[WasteTransferNote] = list(res.scalars().all())
    def url(wtn_id: str) -> str:
        return f"/wtn/{wtn_id}.pdf"
    return {
        "count": len(rows),
        "items": [
            {"id": str(r.id), "created_at": getattr(r, "created_at", None), "pdf_url": url(str(r.id))}
            for r in rows
        ]
    }
