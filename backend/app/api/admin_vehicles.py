from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleRead

router = APIRouter(prefix="/admin/vehicles", tags=["admin:vehicles"])

@router.post("", response_model=VehicleRead, status_code=201)
async def create_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_db)):
    v = Vehicle(**payload.model_dict())
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v

@router.get("", response_model=List[VehicleRead])
async def list_vehicles(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Vehicle).order_by(Vehicle.reg))
    return list(res.scalars())

@router.get("/{vehicle_id}", response_model=VehicleRead)
async def get_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = res.scalar_one_or_none()
    if not v:
        raise HTTPException(404, "vehicle not found")
    return v

@router.patch("/{vehicle_id}", response_model=VehicleRead)
async def update_vehicle(vehicle_id: str, payload: VehicleUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = res.scalar_one_or_none()
    if not v:
        raise HTTPException(404, "vehicle not found")
    for k, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    await db.commit()
    await db.refresh(v)
    return v

@router.delete("/{vehicle_id}", status_code=204)
async def delete_vehicle(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = res.scalar_one_or_none()
    if not v:
        raise HTTPException(404, "vehicle not found")
    await db.delete(v)
    await db.commit()
    return None

