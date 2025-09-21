# path: backend/app/routers/admin/jobs.py

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, admin_gate, engine as async_engine  # async engine
from app.models.job import Base as JobsBase, Job
from app.schemas.job import JobCreate, JobOut, JobPatch  # your Pydantic schemas

router = APIRouter(
    prefix="/admin",
    tags=["admin:jobs"],
    dependencies=[Depends(admin_gate)],
)

async def _ensure_jobs_table() -> None:
    # Why: avoid the sync context manager error inside async paths
    async with async_engine.begin() as conn:
        await conn.run_sync(JobsBase.metadata.create_all)

@router.post("/jobs", response_model=JobOut)
async def create_job_endpoint(payload: JobCreate, db: AsyncSession = Depends(get_db)) -> JobOut:
    await _ensure_jobs_table()
    job = Job(**payload.model_dump(exclude_unset=True))
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return JobOut.model_validate(job)

@router.get("/jobs", response_model=List[JobOut])
async def list_jobs_endpoint(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
) -> List[JobOut]:
    await _ensure_jobs_table()
    stmt = select(Job)
    if status:
        stmt = stmt.where(Job.status == status)
    rows = (await db.execute(stmt.order_by(Job.created_at.desc()))).scalars().all()
    return [JobOut.model_validate(r) for r in rows]

@router.patch("/jobs/{job_id}", response_model=JobOut)
async def patch_job_endpoint(job_id: str, payload: JobPatch, db: AsyncSession = Depends(get_db)) -> JobOut:
    await _ensure_jobs_table()
    changes = payload.model_dump(exclude_unset=True)
    result = await db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(**changes)
        .returning(Job)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.commit()
    return JobOut.model_validate(row[0])
