# path: backend/app/api/drivers.py
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_session
from app.models import models as m
from app.models.driver import DriverProfile, DriverAssignment

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/me")
async def drivers_me(
    session: AsyncSession = Depends(get_session),
    user: m.User = Depends(get_current_user),
):
    if getattr(user, "role", None) != getattr(m.UserRole, "driver", "driver"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Drivers only")

    user_id_s = str(user.id)

    # ensure profile exists
    prof = (
        await session.execute(
            select(DriverProfile).where(DriverProfile.user_id == user_id_s)
        )
    ).scalar_one_or_none()
    if not prof:
        prof = DriverProfile(user_id=user_id_s)
        session.add(prof)
        await session.flush()

    # open assignment (if any)
    assn: Optional[DriverAssignment] = (
        await session.execute(
            select(DriverAssignment).where(
                DriverAssignment.driver_user_id == user_id_s,
                DriverAssignment.open == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()

    open_assignment = None
    if assn:
        skip = (
            await session.execute(
                select(m.Skip).where(m.Skip.id == assn.skip_id)
            )
        ).scalar_one_or_none()
        open_assignment = {
            "id": str(assn.id),
            "status": assn.status,
            "skip_id": str(assn.skip_id),
            "skip_qr_code": getattr(skip, "qr_code", None),
        }

    return {
        "user_id": user_id_s,
        "status": prof.status,
        "updated_at": prof.updated_at,
        "open_assignment": open_assignment,
    }
