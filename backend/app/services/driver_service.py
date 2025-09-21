# backend/app/services/driver_service.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.driver import Driver

async def get_driver(db: AsyncSession, driver_id: str):
    did = str(driver_id)  # <-- force string
    res = await db.execute(select(Driver).where(Driver.id == did))
    return res.scalar_one_or_none()

async def update_driver(db: AsyncSession, driver_id: str, data) -> Driver | None:
    did = str(driver_id)
    res = await db.execute(select(Driver).where(Driver.id == did))
    d = res.scalar_one_or_none()
    if not d:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    await db.flush()
    await db.refresh(d)
    return d
