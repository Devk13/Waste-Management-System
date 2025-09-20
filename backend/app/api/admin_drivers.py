# path: backend/app/api/admin_drivers.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_db

# Resolve model safely – prefer concrete module path
try:
    from app.models.driver import DriverProfile as DriverModel
except Exception:
    from app.models import DriverProfile as DriverModel

from app.api.guards import admin_gate

router = APIRouter(
    prefix="/admin/drivers",
    tags=["admin:drivers"],
    dependencies=[Depends(admin_gate)],
)

# --------- Schemas ---------
class DriverBase(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = True

class DriverCreate(DriverBase):
    name: str = Field(..., min_length=1)

class DriverUpdate(DriverBase):
    pass

class DriverOut(DriverBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


# --------- Helpers ---------
def _set_attrs_safe(obj: Any, data: Dict[str, Any]) -> None:
    for k, v in data.items():
        if v is None:
            continue
        if hasattr(obj, k):
            setattr(obj, k, v)

def _normalize_driver_payload(d: dict) -> dict:
    d = dict(d or {})
    if "name" in d and "full_name" not in d:
        d["full_name"] = d.pop("name")
    return {k: v for k, v in d.items() if v is not None}


# --------- Routes ---------
@router.get("", response_model=List[DriverOut])
async def list_drivers(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Filter by name (contains)"),
):
    stmt = select(DriverModel).order_by(getattr(DriverModel, "created_at", getattr(DriverModel, "id")))
    if q:
        # naive contains if 'name' exists
        try:
            stmt = stmt.where(DriverModel.name.ilike(f"%{q}%"))
        except Exception:
            pass
    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
async def create_driver(
    payload: DriverCreate,
    db: AsyncSession = Depends(get_db),
):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="name required")

    # If your model uses full_name, compare against that
    stmt = select(DriverModel).where(func.lower(DriverModel.full_name) == name.lower())
    exists = (await db.execute(stmt)).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="name already exists")

    drv = DriverModel(
        full_name=name,
        phone=payload.phone,
        license_no=payload.license_no,
        active=bool(payload.active) if payload.active is not None else True,
    )
    db.add(drv)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="name already exists")
    await db.refresh(drv)
    return drv


@router.get("/{driver_id}", response_model=DriverOut)
async def get_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(driver_id)
        stmt = select(DriverModel).where(DriverModel.id == uid)
    except Exception:
        stmt = select(DriverModel).where(DriverModel.id == driver_id)
    res = await db.execute(stmt)
    drv = res.scalar_one_or_none()
    if not drv:
        raise HTTPException(404, "driver not found")
    return drv


@router.patch("/{driver_id}", response_model=DriverOut)
async def update_driver(
    driver_id: str,
    payload: DriverUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        uid = UUID(driver_id)
        stmt = select(DriverModel).where(DriverModel.id == uid)
    except Exception:
        stmt = select(DriverModel).where(DriverModel.id == driver_id)
    res = await db.execute(stmt)
    drv = res.scalar_one_or_none()
    if not drv:
        raise HTTPException(404, "driver not found")

    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    _set_attrs_safe(drv, data)
    await db.commit()
    await db.refresh(drv)
    return drv


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(driver_id)
        stmt = select(DriverModel).where(DriverModel.id == uid)
    except Exception:
        stmt = select(DriverModel).where(DriverModel.id == driver_id)
    res = await db.execute(stmt)
    drv = res.scalar_one_or_none()
    if not drv:
        return  # idempotent
    await db.delete(drv)
    await db.commit()
    return
