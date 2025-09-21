# path: backend/app/api/admin_vehicles.py

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.deps import get_db
from app.api.guards import admin_gate

# Prefer concrete model import; fall back to package re-export if needed
try:
    from app.models.vehicle import Vehicle as VehicleModel
except Exception:
    from app.models import Vehicle as VehicleModel  # type: ignore

router = APIRouter(
    prefix="/admin/vehicles",
    tags=["admin:vehicles"],
    dependencies=[Depends(admin_gate)],
)

# --------- Schemas (self-contained) ---------
class VehicleBase(BaseModel):
    reg_no: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    active: Optional[bool] = True

class VehicleCreate(VehicleBase):
    reg_no: str = Field(min_length=1)

class VehicleUpdate(VehicleBase):
    pass

class VehicleOut(VehicleBase):
    id: str | UUID
    model_config = ConfigDict(from_attributes=True)

# --------- Helpers ---------
def _set_attrs_safe(obj: Any, data: Dict[str, Any]) -> None:
    for k, v in data.items():
        if v is None:
            continue
        if hasattr(obj, k):
            setattr(obj, k, v)

# --------- Routes ---------
@router.get("", response_model=List[VehicleOut])
async def list_vehicles(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Filter by reg_no (contains)"),
):
    stmt = select(VehicleModel).order_by(getattr(VehicleModel, "created_at", getattr(VehicleModel, "id")))
    if q:
        try:
            stmt = stmt.where(VehicleModel.reg_no.ilike(f"%{q}%"))
        except Exception:
            pass
    res = await db.execute(stmt.limit(limit).offset(offset))
    return list(res.scalars().all())

@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def create_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_db)):
    reg = (payload.reg_no or "").strip()
    if not reg:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="reg_no required")

    # case-insensitive unique check
    exists = (await db.execute(
        select(VehicleModel).where(func.lower(VehicleModel.reg_no) == reg.lower())
    )).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="reg_no already exists")

    v = VehicleModel(
        reg_no=reg,
        make=payload.make,
        model=payload.model,
        active=bool(payload.active) if payload.active is not None else True,
    )
    db.add(v)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="reg_no already exists")
    await db.refresh(v)
    return v

@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(vehicle_id)
        stmt = select(VehicleModel).where(VehicleModel.id == uid)
    except Exception:
        stmt = select(VehicleModel).where(VehicleModel.id == vehicle_id)
    v = (await db.execute(stmt)).scalar_one_or_none()
    if not v:
        raise HTTPException(404, "vehicle not found")
    return v

@router.patch("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(VehicleModel, str(vehicle_id))
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="vehicle not found")

    data = payload.model_dump(exclude_unset=True)
    _set_attrs_safe(obj, data)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="duplicate value")

    await db.refresh(obj)
    return obj

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    obj = await db.get(VehicleModel, str(vehicle_id))
    if not obj:
        return  # idempotent
    await db.delete(obj)
    await db.commit()
    return
