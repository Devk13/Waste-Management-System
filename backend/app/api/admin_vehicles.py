# path: backend/app/api/admin_vehicles.py
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, admin_gate
from app.schemas.vehicle import VehicleUpdate, VehicleOut

# Prefer the concrete ORM model exported by your project
try:
    from app.models.vehicle import Vehicle as VehicleModel
except Exception:
    # Fallback if your project re-exports models from the package root
    from app.models import Vehicle as VehicleModel  # type: ignore[misc]

router = APIRouter(
    prefix="/admin/vehicles",
    tags=["admin:vehicles"],
    dependencies=[Depends(admin_gate)],
)

# ---- Local create schema (update/out come from app.schemas.vehicle) ----
from pydantic import BaseModel, Field


class VehicleCreate(BaseModel):
    reg_no: str = Field(..., min_length=1)
    make: Optional[str] = None
    model: Optional[str] = None
    active: Optional[bool] = True


# -------------------- Routes --------------------

@router.get("", response_model=List[VehicleOut])
async def list_vehicles(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Filter by reg_no (contains)"),
):
    stmt = select(VehicleModel)

    if q:
        pattern = f"%{q.lower()}%"
        # case-insensitive contains on reg_no if present
        if hasattr(VehicleModel, "reg_no"):
            stmt = stmt.where(func.lower(getattr(VehicleModel, "reg_no")).like(pattern))

    # Order by created_at if present, otherwise by id
    order_col = getattr(VehicleModel, "created_at", getattr(VehicleModel, "id", None))
    if order_col is not None:
        stmt = stmt.order_by(order_col)

    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def create_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_db)):
    reg = (payload.reg_no or "").strip()
    if not reg:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="reg_no required")

    # Case-insensitive dedupe check
    if hasattr(VehicleModel, "reg_no"):
        exists = (
            await db.execute(
                select(VehicleModel).where(func.lower(getattr(VehicleModel, "reg_no")) == reg.lower())
            )
        ).scalar_one_or_none()
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
    except Exception:
        await db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="create_failed")
    await db.refresh(v)
    return v


@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    # IDs are handled as strings in this project; do not cast to UUID
    obj = await db.get(VehicleModel, str(vehicle_id))
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="vehicle not found")
    return obj


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
    for k, v in data.items():
        setattr(obj, k, v)

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
    if not obj:  # idempotent delete
        return
    await db.delete(obj)
    await db.commit()
    return
