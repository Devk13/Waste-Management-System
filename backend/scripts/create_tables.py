# path: backend/scripts/create_tables.py
import asyncio
from app.db import engine
from app.models.skip import Base as SkipBase
from app.models.labels import Base as LabelsBase

async def main():
    async with engine.begin() as conn:
        # If you share one Base across models, call it once; if not, call for each Base.
        await conn.run_sync(SkipBase.metadata.create_all)
        await conn.run_sync(LabelsBase.metadata.create_all)

asyncio.run(main())
