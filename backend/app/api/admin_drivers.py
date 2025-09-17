from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.driver_admin import DriverCreate, DriverRead

try:
    from app.models.driver import Driver  # your existing table
except Exception as e:
    Driver = None  # type: ignore

router = APIRouter(prefix="/admin/drivers", tags=["admin:drivers"])

@router.post("", response_model=DriverRead, status_code=201)
async def create_driver(payload: DriverCreate, db: AsyncSession = Depends(get_db)):
    if Driver is None:
        raise HTTPException(501, "Driver model not available in this build")
    drv = Driver(name=payload.name)  # Why: use only 'name' to avoid field mismatches
    db.add(drv)
    await db.commit()
    await db.refresh(drv)
    return drv

@router.get("", response_model=List[DriverRead])
async def list_drivers(db: AsyncSession = Depends(get_db)):
    if Driver is None:
        raise HTTPException(501, "Driver model not available in this build")
    res = await db.execute(select(Driver).order_by(Driver.name))
    return list(res.scalars())

