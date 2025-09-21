# path: backend/app/services/jobs_service.py

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobUpdate

async def create_job(db: AsyncSession, data: JobCreate) -> Job:
    job = Job(**data.dict(exclude_unset=True))
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job

async def list_jobs(db: AsyncSession, status: Optional[str] = None, limit: int = 200, offset: int = 0) -> Sequence[Job]:
    stmt = select(Job).order_by(Job.created_at.desc()).limit(limit).offset(offset)
    if status:
        stmt = stmt.where(Job.status == JobStatus(status))
    res = await db.execute(stmt)
    return res.scalars().all()

async def get_job(db: AsyncSession, job_id: str) -> Optional[Job]:
    res = await db.execute(select(Job).where(Job.id == job_id))
    return res.scalar_one_or_none()

async def update_job(db: AsyncSession, job_id: str, data: JobUpdate) -> Optional[Job]:
    job = await get_job(db, job_id)
    if not job:
        return None
    for k, v in data.dict(exclude_unset=True).items():
        setattr(job, k, v)
    await db.flush()
    await db.refresh(job)
    return job

async def jobs_for_driver(db: AsyncSession, driver_id: str) -> Sequence[Job]:
    res = await db.execute(
        select(Job)
        .where(Job.assigned_driver_id == driver_id, Job.status.in_([JobStatus.PENDING, JobStatus.IN_PROGRESS]))
        .order_by(Job.window_start.nulls_last(), Job.created_at.asc())
    )
    return res.scalars().all()

async def mark_done(db: AsyncSession, job_id: str) -> Optional[Job]:
    job = await get_job(db, job_id)
    if not job:
        return None
    job.status = JobStatus.DONE
    await db.flush()
    await db.refresh(job)
    return job
