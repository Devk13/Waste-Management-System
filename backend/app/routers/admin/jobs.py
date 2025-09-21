# path: backend/app/routers/admin/jobs.py

from typing import List, Optional, Callable
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, admin_gate
from app.schemas.job import JobCreate, JobUpdate, JobOut
from app.services.jobs_service import create_job, list_jobs, update_job
from app.models.job import Job

router = APIRouter(
    prefix="/admin/jobs",
    tags=["admin:jobs"],
    dependencies=[Depends(admin_gate)],
)

async def _ensure_jobs_table(db: AsyncSession) -> None:
    # Why: allow running without changing your existing bootstrap.
    bind = db.get_bind()
    assert bind is not None
    async with bind.begin() as conn:
        await conn.run_sync(lambda sync_conn: Job.__table__.create(bind=sync_conn, checkfirst=True))

@router.post("", response_model=JobOut)
async def create_job_endpoint(payload: JobCreate, db: AsyncSession = Depends(get_db)):
    await _ensure_jobs_table(db)
    job = await create_job(db, payload)
    await db.commit()
    return job

@router.get("", response_model=List[JobOut])
async def list_jobs_endpoint(
    status: Optional[str] = Query(None, pattern="^(PENDING|IN_PROGRESS|DONE|FAILED)$"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_jobs_table(db)
    return await list_jobs(db, status=status, limit=limit, offset=offset)

@router.patch("/{job_id}", response_model=JobOut)
async def patch_job_endpoint(job_id: str, payload: JobUpdate, db: AsyncSession = Depends(get_db)):
    await _ensure_jobs_table(db)
    job = await update_job(db, job_id, payload)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.commit()
    return job
