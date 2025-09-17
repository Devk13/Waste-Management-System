from __future__ import annotations
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.skip import Skip
from app.models.contractor import Contractor
from app.models.skip_assignment import SkipAssignment

router = APIRouter(prefix="/admin/bin-assignments", tags=["admin:bins"])

@router.post("/assign")
async def assign_bin(skip_qr: str, contractor_id: str, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    res = await db.execute(select(Skip).where(Skip.qr_code == skip_qr))
    skip = res.scalar_one_or_none()
    if not skip:
        raise HTTPException(404, "skip not found")
    res = await db.execute(select(Contractor).where(Contractor.id == contractor_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "contractor not found")
    # close any active assignment
    res = await db.execute(select(SkipAssignment).where(
        and_(SkipAssignment.skip_id == skip.id, SkipAssignment.unassigned_at.is_(None))
    ))
    active = res.scalar_one_or_none()
    if active:
        active.unassigned_at = func.now()  # type: ignore[name-defined]
    # create a new assignment
    link = SkipAssignment(skip_id=str(skip.id), contractor_id=c.id)
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return {"skip_id": str(skip.id), "contractor_id": c.id, "assignment_id": link.id}

@router.post("/unassign")
async def unassign_bin(skip_qr: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Skip).where(Skip.qr_code == skip_qr))
    skip = res.scalar_one_or_none()
    if not skip:
        raise HTTPException(404, "skip not found")
    res = await db.execute(select(SkipAssignment).where(
        and_(SkipAssignment.skip_id == skip.id, SkipAssignment.unassigned_at.is_(None))
    ))
    active = res.scalar_one_or_none()
    if not active:
        raise HTTPException(404, "no active assignment")
    from sqlalchemy.sql import func
    active.unassigned_at = func.now()
    await db.commit()
    return {"ok": True}

@router.get("/current")
async def get_current_owner(skip_qr: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Skip).where(Skip.qr_code == skip_qr))
    skip = res.scalar_one_or_none()
    if not skip:
        raise HTTPException(404, "skip not found")
    res = await db.execute(select(SkipAssignment, Contractor)
                            .join(Contractor, Contractor.id == SkipAssignment.contractor_id)
                            .where(and_(SkipAssignment.skip_id == skip.id, SkipAssignment.unassigned_at.is_(None))))
    row = res.first()
    if not row:
        return {"skip_id": str(skip.id), "contractor": None}
    link, contractor = row
    return {
        "skip_id": str(skip.id),
        "contractor": {"id": contractor.id, "org_name": contractor.org_name},
        "assigned_at": str(link.assigned_at),
    }

