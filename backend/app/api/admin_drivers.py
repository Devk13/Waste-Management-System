# path: backend/app/api/admin_drivers.py
from __future__ import annotations

from typing import List, Optional

from pydantic.config import ConfigDict
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, admin_gate


# Prefer the concrete model your DB uses (driver_profiles is common in this repo)
try:
    from app.models.driver import DriverProfile as DriverModel
except Exception:
    # fallback if your project exposes `Driver` directly
    from app.models.driver import Driver as DriverModel  # type: ignore[misc]

router = APIRouter(
    prefix="/admin/drivers",
    tags=["admin:drivers"],
    dependencies=[Depends(admin_gate)],
)

# ---- Local create schema  ----
from pydantic import BaseModel, Field


class DriverCreate(BaseModel):
    name: str = Field(min_length=1)
    phone: Optional[str] = None
    license_no: Optional[str] = None
    active: Optional[bool] = True

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    license_no: Optional[str] = None
    active: Optional[bool] = None

class DriverOut(BaseModel):
    id: str
    full_name: str
    phone: Optional[str] = None
    license_no: Optional[str] = None
    active: bool

    # pydantic v2: allow ORM objects to serialize
    model_config = ConfigDict(from_attributes=True)


# -------------------- Routes --------------------

@router.get("", response_model=List[DriverOut])
async def list_drivers(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None, description="Filter by name (contains)"),
):
    stmt = select(DriverModel)

    if q:
        pattern = f"%{q.lower()}%"
        # Try full_name, then name
        if hasattr(DriverModel, "full_name"):
            stmt = stmt.where(func.lower(getattr(DriverModel, "full_name")).like(pattern))
        elif hasattr(DriverModel, "name"):
            stmt = stmt.where(func.lower(getattr(DriverModel, "name")).like(pattern))

    # Order by created_at if present, otherwise by id
    order_col = getattr(DriverModel, "created_at", getattr(DriverModel, "id", None))
    if order_col is not None:
        stmt = stmt.order_by(order_col)

    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
async def create_driver(payload: DriverCreate, db: AsyncSession = Depends(get_db)):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="name required")

    # Uniqueness check on the appropriate column
    col = getattr(DriverModel, "full_name", getattr(DriverModel, "name", None))
    if col is not None:
        exists = (await db.execute(select(DriverModel).where(func.lower(col) == name.lower()))).scalar_one_or_none()
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="name already exists")

    drv_kwargs = {
        "phone": payload.phone,
        "license_no": payload.license_no,
        "active": bool(payload.active) if payload.active is not None else True,
    }
    # Map to the right name column
    if hasattr(DriverModel, "full_name"):
        drv_kwargs["full_name"] = name
    else:
        drv_kwargs["name"] = name

    drv = DriverModel(**drv_kwargs)  # type: ignore[arg-type]
    db.add(drv)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="name already exists")
    except Exception:
        await db.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="create_failed")
    await db.refresh(drv)
    return drv


@router.get("/{driver_id}", response_model=DriverOut)
async def get_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    # Primary keys are stored as strings in this project → never cast to UUID
    obj = await db.get(DriverModel, str(driver_id))
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="driver not found")
    return obj


@router.patch("/{driver_id}", response_model=DriverOut)
async def update_driver(
    driver_id: str,
    payload: DriverUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
):
    obj = await db.get(DriverModel, str(driver_id))
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="driver not found")

    data = payload.model_dump(exclude_unset=True)

    # Normalize 'name' -> 'full_name' if your model uses full_name
    if "name" in data and hasattr(DriverModel, "full_name"):
        data["full_name"] = data.pop("name")

    for k, v in data.items():
        setattr(obj, k, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="duplicate value")

    await db.refresh(obj)
    return obj


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    obj = await db.get(DriverModel, str(driver_id))
    if not obj:  # idempotent delete
        return
    await db.delete(obj)
    await db.commit()
    return

