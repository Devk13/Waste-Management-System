# ======================================================================
# file: backend/app/api/driver_schedule.py
# ======================================================================
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.driver_schedule import DriverTask

router = APIRouter(prefix="/driver", tags=["driver:schedule"])

@router.get("/schedule")
async def get_schedule(
    driver: str = Query(..., min_length=1),
    only_pending: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    q = select(DriverTask).where(DriverTask.driver_name == driver).order_by(DriverTask.scheduled_at.asc())
    rows = (await db.execute(q)).scalars().all()
    items = []
    for r in rows:
        if only_pending and r.done:
            continue
        items.append({
            "id": r.id,
            "task_type": r.task_type,
            "skip_qr": r.skip_qr,
            "to_zone_id": r.to_zone_id,
            "destination_name": r.destination_name,
            "destination_type": r.destination_type,
            "gross_kg": r.gross_kg,
            "tare_kg": r.tare_kg,
            "scheduled_at": str(r.scheduled_at),
            "done": r.done,
            "completed_at": str(r.completed_at) if r.completed_at else None,
        })
    return {"driver": driver, "items": items}

@router.patch("/schedule/{task_id}/done")
async def mark_done(task_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(DriverTask).where(DriverTask.id == task_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "task not found")
    if not row.done:
        row.done = True
        row.completed_at = datetime.utcnow()
        await db.commit()
    return {"ok": True}

# Dev helper to seed a few tasks quickly
@router.post("/dev/schedule/seed")
async def seed_schedule(
    driver: str = Query("Alex"),
    qr: str = Query("QR123"),
    db: AsyncSession = Depends(get_db),
):
    items = [
        DriverTask(driver_name=driver, task_type="deliver-empty", skip_qr=qr, to_zone_id="ZONE_A"),
        DriverTask(driver_name=driver, task_type="relocate-empty", skip_qr=qr, to_zone_id="ZONE_B"),
        DriverTask(driver_name=driver, task_type="collect-full", skip_qr=qr, destination_name="ECO MRF", destination_type="RECYCLING", gross_kg=2500, tare_kg=1500),
        DriverTask(driver_name=driver, task_type="return-empty", skip_qr=qr, to_zone_id="ZONE_C"),
    ]
    db.add_all(items)
    await db.commit()
    return {"created": len(items)}
