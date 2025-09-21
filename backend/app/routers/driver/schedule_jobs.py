# backend/app/routers/driver/schedule_jobs.py

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db, driver_gate
from ...schemas.job import JobOut
from ...services.jobs_service import jobs_for_driver, mark_done
from ...models.job import Job  # needed for checkfirst DDL

router = APIRouter(
    prefix="/driver",
    tags=["driver:schedule"],
    dependencies=[Depends(driver_gate)],
)

async def _ensure_jobs_table(db: AsyncSession) -> None:
    """
    Why: Prevent 500s if the 'jobs' table hasn't been created yet.
    Safe in all envs: CREATE TABLE ... IF NOT EXISTS (checkfirst=True).
    """
    bind = db.get_bind()
    assert bind is not None
    async with bind.begin() as conn:
        await conn.run_sync(lambda sync_conn: Job.__table__.create(bind=sync_conn, checkfirst=True))

@router.get("/schedule", response_model=List[JobOut])
async def driver_schedule(
    driver_id: str = Query(..., description="Temporary MVP: pass driver id until JWT is live."),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_jobs_table(db)
    return await jobs_for_driver(db, driver_id)

@router.patch("/schedule/{task_id}/done", response_model=JobOut)
async def driver_mark_done(task_id: str, db: AsyncSession = Depends(get_db)):
    await _ensure_jobs_table(db)
    job = await mark_done(db, task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.commit()
    return job
