from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.contractor import Contractor
from app.schemas.contractor import ContractorCreate, ContractorUpdate, ContractorRead

router = APIRouter(prefix="/admin/contractors", tags=["admin:contractors"])

@router.post("", response_model=ContractorRead, status_code=201)
async def create_contractor(payload: ContractorCreate, db: AsyncSession = Depends(get_db)):
    c = Contractor(**payload.model_dict())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c

@router.get("", response_model=List[ContractorRead])
async def list_contractors(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Contractor).order_by(Contractor.org_name))
    return list(res.scalars())

@router.get("/{contractor_id}", response_model=ContractorRead)
async def get_contractor(contractor_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Contractor).where(Contractor.id == contractor_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "contractor not found")
    return c

@router.patch("/{contractor_id}", response_model=ContractorRead)
async def update_contractor(contractor_id: str, payload: ContractorUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Contractor).where(Contractor.id == contractor_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "contractor not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    await db.commit()
    await db.refresh(c)
    return c

@router.delete("/{contractor_id}", status_code=204)
async def delete_contractor(contractor_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Contractor).where(Contractor.id == contractor_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "contractor not found")
    await db.delete(c)  # Why: hard delete is simplest for admin
    await db.commit()
    return None

