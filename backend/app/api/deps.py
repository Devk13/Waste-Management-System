# ─────────────────────────────────────────────────────────────────────────────
# path: backend/app/api/deps.py  (DEV fake user w/o importing a User model)
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import uuid
from types import SimpleNamespace
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db import get_session


# Return a lightweight user object with id and role (string). No model import.
def _fake_user_if_enabled():
    role = getattr(settings, "DEBUG_FAKE_ROLE", None)
    if role:
        raw = getattr(settings, "DEBUG_FAKE_USER_ID", None) or "00000000-0000-0000-0000-000000000001"
        try:
            uid = uuid.UUID(str(raw))
        except Exception:
            uid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        return SimpleNamespace(id=uid, role=str(role))
    return None


async def get_current_user(
    session: AsyncSession = Depends(get_session),
):
    fake = _fake_user_if_enabled()
    if fake:
        return fake
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
