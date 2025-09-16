# path: backend/app/api/driver.py
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from collections.abc import AsyncGenerator

# use shared async engine
from ..db import engine

# Ensure related models are registered in the mapper registry
from ..models import labels as _labels  # noqa: F401

# Models: Skip from singular module; driver-specific models in models/driver.py
from ..models.skip import Skip, SkipStatus
from ..models.driver import (
    Movement,
    MovementType,
    SkipPlacement,
    Weight,
    WeightSource,
    Transfer,
    DestinationType,
    WasteTransferNote,
)

router = APIRouter()
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


# -------------------- Schemas (request/response) -----------------------------
class ScanOut(BaseModel):
    id: str
    qr_code: str
    status: Optional[str] = None
    zone_id: Optional[str] = None


class DeliverEmptyIn(BaseModel):
    skip_qr: str
    to_zone_id: str
    driver_name: Optional[str] = None
    vehicle_reg: Optional[str] = None
    note: Optional[str] = None


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # allow ORM -> Pydantic

    id: str
    skip_id: str
    type: MovementType
    from_zone_id: Optional[str] = None
    to_zone_id: Optional[str] = None
    when: datetime


class CollectFullIn(BaseModel):
    skip_qr: str
    destination_type: DestinationType
    destination_name: Optional[str] = None
    destination_address: Optional[str] = None
    commodity_id: Optional[str] = None
    weight_source: WeightSource
    gross_kg: Optional[float] = None
    tare_kg: Optional[float] = None
    net_kg: Optional[float] = None
    driver_name: Optional[str] = None
    vehicle_reg: Optional[str] = None
    gate_pass_ref: Optional[str] = Field(None, description="Stored as movement note")
    site_id: Optional[str] = None


class CollectFullOut(BaseModel):
    movement_id: str
    weight_net_kg: Optional[float]
    transfer_id: str
    wtn_id: Optional[str]


class ReturnEmptyIn(BaseModel):
    skip_qr: str
    to_zone_id: str
    driver_name: Optional[str] = None
    vehicle_reg: Optional[str] = None
    note: Optional[str] = None


class RelocateEmptyIn(BaseModel):
    skip_qr: str
    to_zone_id: str
    driver_name: Optional[str] = None
    vehicle_reg: Optional[str] = None
    note: Optional[str] = None


# --- Dev helper to create a skip locally (bypass auth on /skips) -------------
class EnsureSkipIn(BaseModel):
    qr_code: str
    zone_id: Optional[str] = None


# -------------------- Helpers ------------------------------------------------

def _net(gross: Optional[float], tare: Optional[float], net: Optional[float]) -> Optional[float]:
    if net is not None:
        return net
    if gross is None or tare is None:
        return None
    return max(gross - tare, 0.0)


async def _get_skip_by_qr(db: AsyncSession, qr: str) -> Skip:
    res = await db.execute(select(Skip).where(Skip.qr_code == qr))
    skip = res.scalar_one_or_none()
    if not skip:
        raise HTTPException(404, "skip not found")
    return skip


# -------------------- Endpoints ---------------------------------------------
@router.post("/dev/ensure-skip")
async def dev_ensure_skip(payload: EnsureSkipIn, db: AsyncSession = Depends(get_db)):
    if os.getenv("ENV", "dev").lower() == "prod":
        raise HTTPException(404, "not found")
    try:
        res = await db.execute(select(Skip).where(Skip.qr_code == payload.qr_code))
        skip = res.scalar_one_or_none()
        if not skip:
            skip = Skip(qr_code=payload.qr_code, zone_id=payload.zone_id)
            try:
                skip.status = SkipStatus.IN_STOCK.value  # type: ignore[attr-defined]
            except Exception:
                pass
            db.add(skip)
            await db.commit()
            await db.refresh(skip)
        return {"id": skip.id, "qr_code": skip.qr_code, "status": getattr(skip, "status", None), "zone_id": getattr(skip, "zone_id", None)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"dev_ensure_skip failed: {e.__class__.__name__}: {e}")


@router.get("/scan", response_model=ScanOut)
async def scan(qr: Optional[str] = None, tag: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    qr_val = qr or tag  # support legacy param name
    if not qr_val:
        raise HTTPException(400, "qr is required")
    skip = await _get_skip_by_qr(db, qr_val)
    return ScanOut(id=skip.id, qr_code=skip.qr_code, status=getattr(skip, "status", None), zone_id=getattr(skip, "zone_id", None))


@router.post("/deliver-empty", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
async def deliver_empty(payload: DeliverEmptyIn, db: AsyncSession = Depends(get_db)):
    try:
        skip = await _get_skip_by_qr(db, payload.skip_qr)

        mv = Movement(
            skip_id=skip.id,
            type=MovementType.DELIVERY_EMPTY,
            from_zone_id=None,
            to_zone_id=payload.to_zone_id,
            when=datetime.utcnow(),
            driver_name=payload.driver_name,
            vehicle_reg=payload.vehicle_reg,
            note=payload.note,
        )
        db.add(mv)

        # placement + state
        db.add(SkipPlacement(skip_id=skip.id, zone_id=payload.to_zone_id))
        try:
            skip.status = SkipStatus.DEPLOYED.value  # type: ignore[attr-defined]
        except Exception:
            pass
        skip.zone_id = payload.to_zone_id

        await db.commit()
        await db.refresh(mv)
        return MovementOut.model_validate(mv)
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"deliver-empty failed: {e.__class__.__name__}: {e}")


@router.post("/relocate-empty", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
async def relocate_empty(payload: RelocateEmptyIn, db: AsyncSession = Depends(get_db)):
    skip = await _get_skip_by_qr(db, payload.skip_qr)
    if getattr(skip, "status", None) != SkipStatus.DEPLOYED.value:
        raise HTTPException(400, "skip must be DEPLOYED to relocate")

    mv = Movement(
        skip_id=skip.id,
        type=MovementType.RELOCATION_EMPTY,
        from_zone_id=skip.zone_id,
        to_zone_id=payload.to_zone_id,
        when=datetime.utcnow(),
        driver_name=payload.driver_name,
        vehicle_reg=payload.vehicle_reg,
        note=payload.note,
    )
    db.add(mv)

    # Close current placement
    res = await db.execute(
        select(SkipPlacement)
        .where(SkipPlacement.skip_id == skip.id)
        .where(SkipPlacement.removed_at.is_(None))
        .order_by(SkipPlacement.placed_at.desc())
        .limit(1)
    )
    pl = res.scalar_one_or_none()
    if pl:
        pl.removed_at = datetime.utcnow()

    # Start new placement
    db.add(SkipPlacement(skip_id=skip.id, zone_id=payload.to_zone_id))
    skip.zone_id = payload.to_zone_id

    await db.commit()
    await db.refresh(mv)
    return MovementOut.model_validate(mv)


@router.post("/collect-full", response_model=CollectFullOut, status_code=status.HTTP_201_CREATED)
async def collect_full(payload: CollectFullIn, db: AsyncSession = Depends(get_db)):
    skip = await _get_skip_by_qr(db, payload.skip_qr)
    if getattr(skip, "status", None) not in {SkipStatus.DEPLOYED.value}:
        raise HTTPException(400, "skip not deployed")

    mv = Movement(
        skip_id=skip.id,
        type=MovementType.COLLECTION_FULL,
        from_zone_id=skip.zone_id,
        to_zone_id=None,
        when=datetime.utcnow(),
        driver_name=payload.driver_name,
        vehicle_reg=payload.vehicle_reg,
        note=payload.gate_pass_ref,
    )
    db.add(mv)

    # close placement record
    res = await db.execute(
        select(SkipPlacement)
        .where(SkipPlacement.skip_id == skip.id)
        .where(SkipPlacement.removed_at.is_(None))
        .order_by(SkipPlacement.placed_at.desc())
        .limit(1)
    )
    pl = res.scalar_one_or_none()
    if pl:
        pl.removed_at = datetime.utcnow()

    skip.status = SkipStatus.IN_TRANSIT.value
    skip.zone_id = None

    await db.flush()  # mv.id

    net = _net(payload.gross_kg, payload.tare_kg, payload.net_kg)
    if net is None:
        raise HTTPException(400, "provide gross+tare or net")
    db.add(Weight(movement_id=mv.id, source=payload.weight_source, gross_kg=payload.gross_kg, tare_kg=payload.tare_kg, net_kg=net))

    tr = Transfer(
        movement_id=mv.id,
        site_id=payload.site_id,
        commodity_id=payload.commodity_id,
        destination_type=payload.destination_type,
        destination_name=payload.destination_name,
        destination_address=payload.destination_address,
    )
    db.add(tr)
    await db.flush()  # tr.id

    db.add(
        WasteTransferNote(
            transfer_id=tr.id,
            description=f"Waste from skip {skip.qr_code} -> {payload.destination_type}",
            quantity_kg=net,
            destination_name=payload.destination_name,
        )
    )

    await db.commit()
    return CollectFullOut(movement_id=mv.id, weight_net_kg=net, transfer_id=tr.id, wtn_id=tr.id)


@router.post("/return-empty", response_model=MovementOut, status_code=status.HTTP_201_CREATED)
async def return_empty(payload: ReturnEmptyIn, db: AsyncSession = Depends(get_db)):
    skip = await _get_skip_by_qr(db, payload.skip_qr)
    if getattr(skip, "status", None) == SkipStatus.DEPLOYED.value:
        raise HTTPException(400, "skip already deployed on site")

    mv = Movement(
        skip_id=skip.id,
        type=MovementType.RETURN_EMPTY,
        from_zone_id=None,
        to_zone_id=payload.to_zone_id,
        when=datetime.utcnow(),
        driver_name=payload.driver_name,
        vehicle_reg=payload.vehicle_reg,
        note=payload.note,
    )
    db.add(mv)

    # New placement at the zone
    db.add(SkipPlacement(skip_id=skip.id, zone_id=payload.to_zone_id))
    try:
        skip.status = SkipStatus.DEPLOYED.value  # type: ignore[attr-defined]
    except Exception:
        pass
    skip.zone_id = payload.to_zone_id

    await db.commit()
    await db.refresh(mv)
    return MovementOut.model_validate(mv)
