from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.wtn import WasteTransferNote
from app.services.wtn import build_ctx_form, render_wtn_html, render_wtn_pdf

router = APIRouter(prefix="/wtn", tags=["wtn"])

def _summarize(payload_json: str) -> Dict[str, Any]:
    # Why: give the admin table useful columns without extra joins.
    try:
        payload = json.loads(payload_json or "{}")
    except Exception:
        payload = {}
    ctx = build_ctx_form(payload)
    p1, p2, p3 = ctx.get("part1", {}), ctx.get("part2", {}), ctx.get("part3", {})
    return {
        "quantity": p1.get("quantity") or p3.get("quantity"),
        "waste_type": p1.get("waste_type"),
        "destination": p1.get("destination_location") or p2.get("to_location"),
        "driver_name": p2.get("name"),
        "vehicle_reg": p2.get("plate_no"),
    }

@router.get("", summary="List WTNs (search by id/number prefix)")
async def list_wtns(
    q: Optional[str] = Query(None, description="search by id/number prefix"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    base = select(WasteTransferNote)
    if q:
        # Simple prefix search on id or number
        like = f"{q}%"
        base = base.where(
            (WasteTransferNote.id.like(like)) | (WasteTransferNote.number.like(like))
        )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        await db.execute(
            base.order_by(WasteTransferNote.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
        )
    ).scalars().all()

    items = []
    for r in rows:
        summary = _summarize(r.payload_json or "{}")
        items.append({
            "id": r.id,
            "number": r.number,
            "created_at": str(getattr(r, "created_at", "")),
            **summary,
        })
    return {"items": items, "page": page, "page_size": page_size, "total": total}

@router.get("/{wtn_id}/html", response_class=Response)
async def wtn_html(wtn_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(WasteTransferNote).where(WasteTransferNote.id == wtn_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "wtn not found")
    payload = json.loads(row.payload_json or "{}")
    html = render_wtn_html(build_ctx_form(payload))
    return Response(content=html, media_type="text/html")

@router.get("/{wtn_id}.pdf", response_class=Response)
async def wtn_pdf(wtn_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(WasteTransferNote).where(WasteTransferNote.id == wtn_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "wtn not found")
    payload = json.loads(row.payload_json or "{}")
    html = render_wtn_html(build_ctx_form(payload))
    pdf = render_wtn_pdf(html)
    return Response(content=pdf, media_type="application/pdf")
