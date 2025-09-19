# path: backend/app/api/wtn.py
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc

from app.api.deps import get_db
from app.models.driver import WasteTransferNote

router = APIRouter(tags=["wtn"])

# --- optional PDF engine (WeasyPrint) ---
try:  # why: MVP gracefully falls back to HTML if not present
    from weasyprint import HTML, CSS  # type: ignore
    _HAS_PDF = True
except Exception:
    HTML = CSS = None  # type: ignore
    _HAS_PDF = False


def _esc(s: Optional[str]) -> str:
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _fmt_dt(dt: Any) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt or "")


def _render_html(ctx: Dict[str, Any]) -> str:
    """
    Minimal, printable HTML approximating the sample card:
    - PART 1 (Originator): light gray
    - PART 2 (Transporter): peach
    - PART 3 (Receiver): light green
    """
    # lines are styled with dotted borders; values injected next to labels
    return f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>WTN {ctx['wtn_id']}</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
  @page {{ size: A4; margin: 16mm; }}
  :root {{
    --border:#000;
    --part1:#f3f4f6; /* gray-100 */
    --part2:#fde7d9; /* soft peach */
    --part3:#e7f7e7; /* soft green */
    --label:#111827;
  }}
  body {{
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Arial, sans-serif;
    color:#111; font-size:12px;
  }}
  .sheet {{ border:1px solid var(--border); }}
  .row {{ display:grid; grid-template-columns: 40px 1fr; border-bottom:1px solid var(--border); }}
  .part-label {{
    writing-mode: vertical-rl; text-orientation: mixed;
    font-weight:700; letter-spacing:1px; text-align:center; padding:8px 4px;
    border-right:1px solid var(--border);
  }}
  .section {{ padding:10px 12px 12px; }}
  .title {{ font-weight:800; letter-spacing:.5px; margin:2px 0 8px; }}
  .p1 {{ background:var(--part1); }}
  .p2 {{ background:var(--part2); }}
  .p3 {{ background:var(--part3); }}
  .field {{ margin:6px 0; }}
  .label {{ color:var(--label); font-weight:700; }}
  .line {{
    display:inline-block; min-width:140px; border-bottom:1px dotted #444; padding:0 4px;
  }}
  .grid-2 {{ display:grid; grid-template-columns: 1fr 1fr; gap:8px; }}
  .grid-3 {{ display:grid; grid-template-columns: 1fr 1fr 1fr; gap:8px; }}
  .footer {{ font-size:10px; color:#555; margin-top:8px; }}
</style>
</head>
<body>
  <div class="sheet">
    <!-- PART 1 ORIGINATOR -->
    <div class="row p1">
      <div class="part-label">P A R T<br/>1</div>
      <div class="section">
        <div class="title">WASTE ORIGINATOR</div>
        <div class="field">
          I CONFIRM THAT <span class="line">{ctx['qty_str']}</span> (QUANTITY) OF
          <span class="line">{ctx['waste_type']}</span> TYPE OF WASTE WAS
        </div>
        <div class="field">
          LOADED ON <span class="line">{ctx['loaded_at']}</span> (DATE &amp; TIME) FROM
        </div>
        <div class="field">
          <span class="line" style="min-width:420px">{ctx['origin_loc']}</span> (ORIGINATOR LOCATION) AND WILL BE
        </div>
        <div class="field">
          TRANSPORTED TO <span class="line" style="min-width:420px">{ctx['dest_loc']}</span> AS APPROVED LOCATION.
        </div>
        <div class="grid-3">
          <div class="field"><span class="label">NAME:</span> <span class="line">{ctx['origin_name']}</span></div>
          <div class="field"><span class="label">ID NO.:</span> <span class="line">{ctx['origin_id']}</span></div>
          <div class="field"><span class="label">SIGNATURE:</span> <span class="line">&nbsp;</span></div>
        </div>
        <div class="field"><span class="label">TEL NO.:</span> <span class="line">{ctx['origin_tel']}</span></div>
      </div>
    </div>

    <!-- PART 2 TRANSPORTER -->
    <div class="row p2">
      <div class="part-label">P A R T<br/>2</div>
      <div class="section">
        <div class="title">WASTE TRANSPORTER</div>
        <div class="field">
          I SHALL TRANSPORT THE AFOREMENTIONED WASTE TO
          <span class="line" style="min-width:420px">{ctx['dest_loc']}</span> (Location).
        </div>
        <div class="field"><span class="label">COMPANY NAME:</span> <span class="line" style="min-width:300px">{ctx['carrier_company']}</span></div>
        <div class="grid-3">
          <div class="field"><span class="label">NAME:</span> <span class="line">{ctx['carrier_name']}</span></div>
          <div class="field"><span class="label">ID / IQAMA NO.:</span> <span class="line">{ctx['carrier_id']}</span></div>
          <div class="field"><span class="label">SIGNATURE:</span> <span class="line">&nbsp;</span></div>
        </div>
        <div class="grid-3">
          <div class="field"><span class="label">TEL NO.:</span> <span class="line">{ctx['carrier_tel']}</span></div>
          <div class="field"><span class="label">PLATE NO.:</span> <span class="line">{ctx['vehicle_plate']}</span></div>
          <div class="field"><span class="label">WTN ID:</span> <span class="line">{ctx['wtn_id']}</span></div>
        </div>
      </div>
    </div>

    <!-- PART 3 RECEIVER -->
    <div class="row p3">
      <div class="part-label">P A R T<br/>3</div>
      <div class="section">
        <div class="title">WASTE RECEIVER</div>
        <div class="field">
          I CONFIRM RECEIPT OF THE STATED WASTE <span class="line">{ctx['qty_str']}</span> (QUANTITY) ON
        </div>
        <div class="field">
          <span class="line">{ctx['received_at']}</span> (DATE &amp; TIME) AT ABOVE LOCATION AND WILL DISPOSE OF/TREAT
        </div>
        <div class="field">THE WASTE AS APPROVED. DISPOSAL/ TREATMENT IS <span class="line" style="min-width:420px">{ctx['treatment']}</span></div>
        <div class="grid-3">
          <div class="field"><span class="label">NAME</span> <span class="line">{ctx['receiver_name']}</span></div>
          <div class="field"><span class="label">ID/IQAMA NO.</span> <span class="line">{ctx['receiver_id']}</span></div>
          <div class="field"><span class="label">SIGNATURE OF RECEIVER &amp; STAMP</span> <span class="line" style="min-width:200px">&nbsp;</span></div>
        </div>
      </div>
    </div>

    <div class="section footer">
      Generated: {ctx['created_at']} • Transfer #{ctx['transfer_id']}
    </div>
  </div>
</body>
</html>
""".strip()


async def _get_wtn(db: AsyncSession, wtn_id: str) -> WasteTransferNote | None:
    """
    Be tolerant to how the PK is stored:
    - Some DBs store UUID as TEXT (with dashes)
    - Some store as BLOB/UUID type
    - Some store hex (without dashes)
    We try raw str, UUID object, then uuid.hex as str.
    """
    # 1) try raw string
    try:
        res = await db.execute(select(WasteTransferNote).where(WasteTransferNote.id == wtn_id))
        row = res.scalar_one_or_none()
        if row:
            return row
    except Exception:
        pass

    # 2) try UUID object + 3) hex form
    try:
        from uuid import UUID
        uid = UUID(wtn_id)
        # 2a) compare with UUID-typed value
        try:
            res = await db.execute(select(WasteTransferNote).where(WasteTransferNote.id == uid))
            row = res.scalar_one_or_none()
            if row:
                return row
        except Exception:
            pass

        # 2b) compare with hex string (no dashes)
        try:
            res = await db.execute(select(WasteTransferNote).where(WasteTransferNote.id == uid.hex))
            row = res.scalar_one_or_none()
            if row:
                return row
        except Exception:
            pass
    except Exception:
        pass

    return None


def _ctx_from_wtn(wtn: WasteTransferNote) -> Dict[str, Any]:
    qty = getattr(wtn, "quantity_kg", None)
    qty_str = f"{qty:,.2f} kg" if isinstance(qty, (int, float)) else ""
    return {
        "wtn_id": str(getattr(wtn, "id", "")),
        "transfer_id": str(getattr(wtn, "transfer_id", "")),
        "created_at": _fmt_dt(getattr(wtn, "created_at", None)),
        "qty_str": qty_str,
        "waste_type": _esc(getattr(wtn, "description", "") or "MIXED WASTE"),
        "origin_loc": _esc(getattr(wtn, "producer_name", "") or "ORIGINATOR SITE"),
        "dest_loc": _esc(getattr(wtn, "destination_name", "") or "APPROVED LOCATION"),
        "treatment": _esc(getattr(wtn, "ewc_code", "") or "APPROVED METHOD"),
        # transporter bits we store today
        "carrier_company": _esc(getattr(wtn, "carrier_name", "") or "CARRIER CO."),
        "carrier_name": _esc(getattr(wtn, "carrier_name", "") or "Driver"),
        "vehicle_plate": "",  # fill later from vehicle when joined
        # placeholders for signature/id/tel (add joins later)
        "origin_name": "", "origin_id": "", "origin_tel": "",
        "carrier_id": "", "carrier_tel": "",
        "receiver_name": "", "receiver_id": "",
        "loaded_at": _fmt_dt(getattr(wtn, "created_at", None)),
        "received_at": _fmt_dt(getattr(wtn, "created_at", None)),
    }


@router.get("/wtn/{wtn_id}.pdf")
async def get_wtn_pdf_or_html(
    wtn_id: str = Path(..., description="WTN identifier (UUID or string)"),
    format: str = Query("pdf", pattern="^(pdf|html)$", description="pdf or html"),
    as_attachment: bool = Query(False, description="force download"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns PDF if WeasyPrint is installed and `format=pdf`, else HTML.
    """
    wtn = await _get_wtn(db, wtn_id)
    if not wtn:
        raise HTTPException(status_code=404, detail="WTN not found")

    ctx = _ctx_from_wtn(wtn)
    html = _render_html(ctx)

    want_pdf = (format == "pdf")
    if want_pdf and _HAS_PDF:
        # Inline CSS already in the HTML; you can add CSS() files here if needed.
        pdf_bytes = HTML(string=html).write_pdf()  # type: ignore
        disp = 'attachment' if as_attachment else 'inline'
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'{disp}; filename="wtn-{ctx["wtn_id"]}.pdf"'},
        )

    # Fallback HTML (or explicit format=html)
    disp = 'attachment' if as_attachment else 'inline'
    return HTMLResponse(
        html,
        headers={"Content-Disposition": f'{disp}; filename="wtn-{ctx["wtn_id"]}.html"'},
    )

@router.get("/__debug/wtns")
async def debug_list_wtns(limit: int = 10, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(WasteTransferNote).order_by(desc(WasteTransferNote.created_at)).limit(limit)
    )
    out = []
    for w in res.scalars().all():
        out.append({
            "id": str(getattr(w, "id", "")),
            "transfer_id": str(getattr(w, "transfer_id", "")),
            "created_at": str(getattr(w, "created_at", "")),
            "quantity_kg": getattr(w, "quantity_kg", None),
            "destination_name": getattr(w, "destination_name", None),
        })
    return out
