from fastapi import APIRouter
from datetime import datetime
import os

router = APIRouter()

@router.get("/__smoke", summary="Skips router smoke probe")
async def skips_smoke():
    # Why: proves /skips router is mounted without touching DB
    return {
        "ok": True,
        "ts": datetime.utcnow().isoformat() + "Z",
        "env": os.getenv("ENV", "dev"),
        "note": "If you see this, /skips is mounted.",
    }
