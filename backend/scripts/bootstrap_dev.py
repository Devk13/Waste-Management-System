# backend/scripts/bootstrap_dev.py
from pathlib import Path; import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

import asyncio
from app.db import engine
from app.models.skip import Base as SkipBase
from app.models.labels import Base as LabelsBase
from app.models.driver import Base as DriverBase
try:
    from app.models.base import Base as CoreBase  # movements/weights/transfers/wtns
except Exception:
    CoreBase = None  # type: ignore

async def main():
    groups = [("skips", SkipBase), ("labels", LabelsBase), ("driver", DriverBase)]
    if CoreBase is not None: groups.append(("core", CoreBase))
    async with engine.begin() as conn:
        for name, Base in groups:
            await conn.run_sync(Base.metadata.create_all)
            print("created:", name)

asyncio.run(main())
