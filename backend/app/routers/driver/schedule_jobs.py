# path: backend/app/routers/driver/schedule_jobs.py
from __future__ import annotations
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db, driver_gate
from ...schemas.job import JobOut
from ...services.jobs_service import jobs_for_driver, mark_done
from ...models.job import Job

log = logging.getLogger("uvicorn")

router = APIRouter(
    prefix="/driver",
    tags=["driver:schedule"],
    dependencies=[Depends(driver_gate)],
)

async def _ensure_jobs_table(db: AsyncSession) -> None:
    bind = db.get_bind()
    assert bind is not None
    async with bind.begin() as conn:
        await conn.run_sync(lambda s: Job.__table__.create(bind=s, checkfirst=True))

@router.get("/schedule", response_model=List[JobOut])
async def driver_schedule(
    driver_id: Optional[str] = Query(None, description="Preferred param"),
    driver:    Optional[str] = Query(None, description="Legacy alias"),
    db: AsyncSession = Depends(get_db),
) -> List[JobOut]:
    await _ensure_jobs_table(db)
    did = (driver_id or driver or "").strip()
    if not did:
        raise HTTPException(
            status_code=422,
            detail=[{"type":"missing","loc":["query","driver|driver_id"],"msg":"Field required","input":None}],
        )
    try:
        rows = await jobs_for_driver(db, did)  # likely returns ORM rows
        return [JobOut.model_validate(r) for r in rows]
    except Exception as e:
        log.exception("driver_schedule failed for driver_id=%s: %s", did, e)
        raise HTTPException(status_code=500, detail=f"driver_schedule failed: {type(e).__name__}: {e}")

@router.patch("/schedule/{task_id}/done", response_model=JobOut)
async def driver_mark_done(task_id: str, db: AsyncSession = Depends(get_db)) -> JobOut:
    await _ensure_jobs_table(db)
    try:
        job = await mark_done(db, task_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        await db.commit()
        return JobOut.model_validate(job)
    except HTTPException:
        raise
    except Exception as e:
        log.exception("driver_mark_done failed id=%s: %s", task_id, e)
        raise HTTPException(status_code=500, detail=f"driver_mark_done failed: {type(e).__name__}: {e}")
