# path: backend/app/api/driver.py
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from types import SimpleNamespace
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, Body, Query, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

# Core models we know exist
from app.models import Skip, SkipStatus
from app.models.driver import (
    Movement, MovementType,
    Weight, WeightSource,
    Transfer, DestinationType,
    WasteTransferNote,
)

router = APIRouter(tags=["driver"])

# ===================== Schemas (outputs) =====================
class ScanOut(BaseModel):
    id: str
    qr_code: str
    status: Optional[str] = None
    zone_id: Optional[str] = None

class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    skip_id: str
    type: MovementType
    from_zone_id: Optional[str] = None
    to_zone_id: Optional[str] = None
    when: datetime

class CollectFullOut(BaseModel):
    movement_id: str
    weight_net_kg: Optional[float]
    transfer_id: str
    wtn_id: Optional[str]
    wtn_pdf_url: Optional[str] = None

class ReturnEmptyOut(BaseModel):
    movement_id: str
    skip_id: str
    to_zone_id: str
    placement_id: str | None = None
    status: str | None = None

# ===================== Helpers =====================
def get_str(d: Dict[str, Any] | None, *keys: str) -> Optional[str]:
    if not d: return None
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None

def get_num(d: Dict[str, Any] | None, *keys: str) -> Optional[float]:
    if not d: return None
    for k in keys:
        v = d.get(k)
        if v in (None, ""): continue
        try: return float(v)
        except Exception: continue
    return None

def parse_enum(enum_cls, value: Optional[str], default=None):
    if value is None: return default
    s = str(value).strip().lower()
    for m in enum_cls:
        if m.name.lower() == s or str(getattr(m, "value", "")).lower() == s:
            return m
    return default

async def _get_skip_by_qr(db: AsyncSession, qr: str) -> Skip:
    res = await db.execute(select(Skip).where(Skip.qr_code == qr))
    skip = res.scalar_one_or_none()
    if not skip: raise HTTPException(404, "skip not found")
    return skip

@lru_cache(maxsize=1)
def _get_placement_model():
    """
    Resolve SkipPlacement safely:
    - Try app.models.SkipPlacement
    - Try app.models.models.SkipPlacement
    If not found, return None and helpers will no-op/fallback.
    """
    try:
        from app.models import SkipPlacement as SP  # type: ignore
        if SP is not None:
            return SP
    except Exception:
        pass
    try:
        from app.models import models as mm  # type: ignore
        SP = getattr(mm, "SkipPlacement", None)
        if SP is not None:
            return SP
    except Exception:
        pass
    return None

async def _get_active_placement(db: AsyncSession, *, skip: Skip):
    """
    Return active placement row if model is available, otherwise a
    lightweight fallback using skip.zone_id to keep the flow moving.
    """
    PM = _get_placement_model()
    if PM is None:
        # fallback: treat zone_id as current placement indicator
        if getattr(skip, "zone_id", None):
            return SimpleNamespace(zone_id=skip.zone_id)
        return None

    res = await db.execute(
        select(PM)
        .where(PM.skip_id == skip.id)
        .where(PM.removed_at.is_(None))
        .order_by(PM.placed_at.desc())
        .limit(1)
    )
    return res.scalars().first()

async def _close_all_active_placements(db: AsyncSession, *, skip: Skip, when: datetime) -> None:
    """Close open placements if model exists; otherwise no-op."""
    PM = _get_placement_model()
    if PM is None:
        return
    res = await db.execute(
        select(PM)
        .where(PM.skip_id == skip.id)
        .where(PM.removed_at.is_(None))
    )
    for pl in res.scalars().all():
        pl.removed_at = when

async def _open_placement(db: AsyncSession, *, skip: Skip, zone_id: Optional[str], when: datetime) -> None:
    """Open a placement if model exists and zone provided."""
    PM = _get_placement_model()
    if PM is None or not zone_id:
        return
    db.add(PM(skip_id=skip.id, zone_id=zone_id, placed_at=when))

def _calc_net(g: Optional[float], t: Optional[float], n: Optional[float]) -> Optional[float]:
    if n is not None:
        try: return float(n)
        except Exception: return None
    if g is not None and t is not None:
        try: return float(g) - float(t)
        except Exception: return None
    return None

async def _safe_place(db: AsyncSession, *, skip: Skip, to_zone_id: Optional[str], when: datetime, movement_type: MovementType) -> None:
    """Best-effort placement + state update; never raises."""
    try:
        await _close_all_active_placements(db, skip=skip, when=when)
        await _open_placement(db, skip=skip, zone_id=to_zone_id, when=when)
        skip.zone_id = to_zone_id
        try:
            if movement_type in (MovementType.DELIVERY_EMPTY, MovementType.RETURN_EMPTY):
                skip.status = getattr(SkipStatus, "DEPLOYED", SkipStatus).value
            elif movement_type == MovementType.COLLECTION_FULL:
                skip.status = getattr(SkipStatus, "IN_TRANSIT", SkipStatus).value
        except Exception:
            pass
    except Exception as e:
        print(f"[place] best-effort failed: {e.__class__.__name__}: {e}", flush=True)

# ===================== Endpoints =====================
@router.api_route("/scan", methods=["GET", "POST"], response_model=ScanOut)
async def scan(
    qr: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    payload: Dict[str, Any] | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    code = qr or q or get_str(payload, "qr", "q")
    if not code: raise HTTPException(400, "qr is required")
    skip = await _get_skip_by_qr(db, code)
    return {"id": str(skip.id), "qr_code": skip.qr_code, "status": getattr(skip, "status", None), "zone_id": getattr(skip, "zone_id", None)}

@router.post("/deliver-empty", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
async def deliver_empty(payload: Dict[str, Any] = Body(...), db: AsyncSession = Depends(get_db)):
    skip_qr = get_str(payload, "skip_qr", "qr", "skipId", "skip_id")
    to_zone_id = get_str(payload, "to_zone_id", "zone_id", "toZoneId")
    if not skip_qr or not to_zone_id: raise HTTPException(400, "skip_qr and to_zone_id required")
    skip = await _get_skip_by_qr(db, skip_qr)

    when = datetime.utcnow()
    mv = Movement(
        skip_id=skip.id, type=MovementType.DELIVERY_EMPTY,
        from_zone_id=None, to_zone_id=to_zone_id, when=when,
        driver_name=get_str(payload, "driver_name", "driver"),
        vehicle_reg=get_str(payload, "vehicle_reg", "vehicle", "vehicle_reg_no"),
        note=get_str(payload, "note"),
    )
    db.add(mv)
    await _safe_place(db, skip=skip, to_zone_id=to_zone_id, when=when, movement_type=MovementType.DELIVERY_EMPTY)
    await db.commit(); await db.refresh(mv)
    return MovementOut.model_validate(mv)

@router.post("/relocate-empty", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
async def relocate_empty(payload: Dict[str, Any] = Body(...), db: AsyncSession = Depends(get_db)):
    skip_qr = get_str(payload, "skip_qr", "qr", "skipId", "skip_id")
    to_zone_id = get_str(payload, "to_zone_id", "zone_id", "toZoneId")
    if not skip_qr or not to_zone_id: raise HTTPException(400, "skip_qr and to_zone_id required")
    skip = await _get_skip_by_qr(db, skip_qr)

    when = datetime.utcnow()
    mv = Movement(
        skip_id=skip.id, type=MovementType.RELOCATION_EMPTY,
        from_zone_id=getattr(skip, "zone_id", None), to_zone_id=to_zone_id, when=when,
        driver_name=get_str(payload, "driver_name", "driver"),
        vehicle_reg=get_str(payload, "vehicle_reg", "vehicle", "vehicle_reg_no"),
        note=get_str(payload, "note"),
    )
    db.add(mv)
    await _safe_place(db, skip=skip, to_zone_id=to_zone_id, when=when, movement_type=MovementType.RELOCATION_EMPTY)
    await db.commit(); await db.refresh(mv)
    return MovementOut.model_validate(mv)

@router.post("/collect-full", response_model=CollectFullOut, status_code=status.HTTP_201_CREATED)
async def collect_full(payload: Dict[str, Any] = Body(...), db: AsyncSession = Depends(get_db)):
    skip_qr = get_str(payload, "skip_qr", "qr", "skipId", "skip_id")
    if not skip_qr: raise HTTPException(400, "skip_qr (or qr) required")
    skip = await _get_skip_by_qr(db, skip_qr)

    # Require "active placement" or fallback via zone_id when model missing
    active = await _get_active_placement(db, skip=skip)
    if not active:
        raise HTTPException(400, "skip not deployed on a site")

    when = datetime.utcnow()
    mv = Movement(
        skip_id=skip.id, type=MovementType.COLLECTION_FULL,
        from_zone_id=getattr(active, "zone_id", None), to_zone_id=None, when=when,
        driver_name=get_str(payload, "driver_name", "driver"),
        vehicle_reg=get_str(payload, "vehicle_reg", "vehicle", "vehicle_reg_no"),
        note=get_str(payload, "gate_pass_ref", "note"),
    )
    db.add(mv)

    # Close placements + set state safely (model may be absent; helpers handle it)
    await _safe_place(db, skip=skip, to_zone_id=None, when=when, movement_type=MovementType.COLLECTION_FULL)
    await db.flush()  # mv.id

    gross = get_num(payload, "gross_kg", "gross")
    tare  = get_num(payload, "tare_kg", "tare")
    net   = get_num(payload, "net_kg", "net")
    net_val = _calc_net(gross, tare, net) or 0.0

    w = Weight(
        movement_id=mv.id,
        source=parse_enum(WeightSource, str(payload.get("weight_source", "")), default=WeightSource.WEIGHBRIDGE),
        gross_kg=gross, tare_kg=tare, net_kg=net_val,
    )
    db.add(w)

    tr = Transfer(
        movement_id=mv.id,
        site_id=get_str(payload, "site_id") or "SITE-DEV",
        commodity_id=get_str(payload, "commodity_id") or "COM-DEV",
        destination_type=parse_enum(DestinationType, str(payload.get("destination_type", "")), default=DestinationType.RECYCLING),
        destination_name=get_str(payload, "destination_name", "dest_name") or "ECO MRF",
        destination_address=get_str(payload, "destination_address"),
    )
    db.add(tr); await db.flush()

    wtn = WasteTransferNote(
        transfer_id=str(tr.id),
        description=f"Collection of skip {getattr(skip, 'qr_code', '')}",
        ewc_code=None, quantity_kg=float(net_val),
        producer_name=None,
        carrier_name=get_str(payload, "driver_name", "driver"),
        destination_name=tr.destination_name,
        created_at=datetime.utcnow(),
    )
    db.add(wtn)
    await db.flush()

    # COMMIT so /wtn/{id}.pdf (new session) can read the row
    await db.commit()

    return {
        "movement_id": str(mv.id),
        "weight_net_kg": float(net_val),
        "transfer_id": str(tr.id),
        "wtn_id": str(wtn.id),
        "wtn_pdf_url": f"/wtn/{wtn.id}.pdf",
    }

@router.post("/return-empty", response_model=ReturnEmptyOut, status_code=status.HTTP_201_CREATED)
async def return_empty(payload: Dict[str, Any] = Body(...), db: AsyncSession = Depends(get_db)):
    skip_qr = get_str(payload, "skip_qr", "qr", "skipId", "skip_id")
    to_zone_id = get_str(payload, "to_zone_id", "zone_id", "toZoneId")
    if not skip_qr or not to_zone_id:
        raise HTTPException(400, "skip_qr and to_zone_id required")

    skip = await _get_skip_by_qr(db, skip_qr)
    when = datetime.utcnow()

    mv = Movement(
        skip_id=skip.id,
        type=MovementType.RETURN_EMPTY,
        from_zone_id=None,
        to_zone_id=to_zone_id,
        when=when,
        driver_name=get_str(payload, "driver_name", "driver"),
        vehicle_reg=get_str(payload, "vehicle_reg", "vehicle", "vehicle_reg_no"),
    )
    db.add(mv)

    # Best-effort: open new placement + set status
    await _safe_place(db, skip=skip, to_zone_id=to_zone_id, when=when, movement_type=MovementType.RETURN_EMPTY)

    # Ensure IDs are available
    await db.flush()   # mv.id + any new placement id

    # Try to fetch the most recent placement as the one we just opened
    placement_id: str | None = None
    PM = _get_placement_model()
    if PM is not None:
        res = await db.execute(
            select(PM)
            .where(PM.skip_id == skip.id)
            .order_by(PM.placed_at.desc())
            .limit(1)
        )
        last_pl = res.scalars().first()
        if last_pl:
            placement_id = str(getattr(last_pl, "id", None))

    return ReturnEmptyOut(
        movement_id=str(mv.id),
        skip_id=str(skip.id),
        to_zone_id=to_zone_id,
        placement_id=placement_id,
        status=getattr(skip, "status", None),
    )
