from __future__ import annotations
import uuid
from typing import Any, Optional
import os
from fastapi import APIRouter                                               #delete
from fastapi import APIRouter, Depends, Header, HTTPException, status       #delete
from pydantic import BaseModel                                              #delete
from sqlalchemy import select                                               #delete
from sqlalchemy.ext.asyncio import AsyncSession                             #delete
from app.core.config import settings                                        #delete
from app.db import get_session                                              #delete
from app.models import models as m                                          #delete
from app.models.models import Skip

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.core.config import settings
from app.db import get_session
from app.models.skip import Skip
from app.models.labels import SkipAsset, SkipAssetKind
from app.schemas.skip import SkipCreate, SkipOut
from app.services.qr_labels import LabelMeta, make_qr_png, make_three_up_pdf

# Optional Organization support (skip gracefully if your model isn’t present)
try:
    from app.models.organization import Organization  # type: ignore
except Exception:  # pragma: no cover
    Organization = None  # type: ignore

router = APIRouter(prefix="/skips", tags=["skips"])

# ---------------------------------------------------------------------------
# TEMP smoke-test helper: /skips/_seed (guarded by ADMIN_API_KEY)
# Remove this endpoint and the ADMIN_API_KEY env var after your smoke tests.
# ---------------------------------------------------------------------------

def _admin_key_ok(x_api_key: str | None = Header(None)) -> None:
    if not settings.ADMIN_API_KEY or x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

class _SeedSkip(BaseModel):
    owner_org_id: str
    qr_code: str
    size: str | None = None
    color: str | None = None
    notes: str | None = None

@router.post("/_seed", status_code=201, tags=["dev"])
async def seed_skip(
    payload: _SeedSkip,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(_admin_key_ok),
):
    # if a skip with this qr_code already exists, just return its id (idempotent seed)
    existing = (
        await session.execute(select(m.Skip).where(m.Skip.qr_code == payload.qr_code))
    ).scalar_one_or_none()
    if existing:
        return {"id": str(existing.id), "created": False}

    new_skip = m.Skip(
        owner_org_id=payload.owner_org_id,
        qr_code=payload.qr_code,
        size=payload.size,
        color=payload.color,
        notes=payload.notes,
    )
    session.add(new_skip)
    await session.flush()
    await session.commit()
    return {"id": str(new_skip.id), "created": True}

# --------------------------------------------------------------------------- endpoint

# DEV seed payload (typed for clarity)
class SeedIn(BaseModel):
    owner_org_id: str
    qr_code: str
    size: str | None = None
    color: str | None = None
    notes: str | None = None

@router.post("/_seed", status_code=201, tags=["dev"])
async def seed_skip(
    body: SeedIn,
    session: AsyncSession = Depends(get_session),
    x_api_key: str | None = Header(None, convert_underscores=False),
):
    # auth
    from app.core.config import settings
    if not x_api_key or x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    # idempotent by qr_code
    existing = (
        await session.execute(select(m.Skip).where(m.Skip.qr_code == body.qr_code))
    ).scalar_one_or_none()
    if existing:
        return {"id": str(existing.id), "qr_code": existing.qr_code}

    s = m.Skip(
        owner_org_id=body.owner_org_id,
        qr_code=body.qr_code,
        size=body.size,
        color=body.color,
        notes=body.notes,
    )
    session.add(s)
    await session.flush()
    return {"id": str(s.id), "qr_code": s.qr_code}


def _qr_deeplink(code: str) -> str:
    base = settings.DRIVER_QR_BASE_URL
    if base:
        return f"{base.rstrip('/')}/driver/qr/{code}"
    return code


@router.post("", response_model=SkipOut, status_code=201)
async def create_skip(
    payload: SkipCreate,
    session: AsyncSession = Depends(get_session),
    user: Any = Depends(get_current_user),
):
    # Admin-only
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")

    # Resolve org name (optional)
    org_name: str = "OWNER"
    if Organization is not None:
        org = (
            await session.execute(
                select(Organization).where(Organization.id == payload.owner_org_id)  # type: ignore[attr-defined]
            )
        ).scalar_one_or_none()
        if not org:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Owner org not found")
        org_name = getattr(org, "name", org_name)

    # qr_code (unique)
    qr_code = payload.qr_code or ("SK-" + uuid.uuid4().hex[:8].upper())
    exists = (
        await session.execute(select(Skip).where(Skip.qr_code == qr_code))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="qr_code already exists")

    # ── IMPORTANT: cast UUIDs → str for SQLite-safe inserts ───────────────
    owner_org_id = str(payload.owner_org_id)
    assigned_id = (
        str(payload.assigned_commodity_id) if payload.assigned_commodity_id else None
    )
    zone_id = str(payload.zone_id) if payload.zone_id else None
    user_id = str(getattr(user, "id", "")) or None

    skip = Skip(
        qr_code=qr_code,
        owner_org_id=owner_org_id,
        assigned_commodity_id=assigned_id,
        zone_id=zone_id,
        created_by_id=user_id,
        updated_by_id=user_id,
    )
    session.add(skip)
    await session.flush()  # get skip.id

    # Generate assets
    deeplink = _qr_deeplink(qr_code)
    png_bytes = make_qr_png(deeplink)
    meta = LabelMeta(qr_text=deeplink, qr_code=qr_code, org_name=org_name)
    pdf_bytes = make_three_up_pdf(meta, png_bytes)

    # Store 3 PNGs + 1 PDF (skip_id must be string if your SkipAsset.skip_id is String)
    for i in range(1, 4):
        session.add(
            SkipAsset(
                skip_id=str(skip.id),
                kind=SkipAssetKind.label_png,
                idx=i,
                content_type="image/png",
                data=png_bytes,
            )
        )

    session.add(
        SkipAsset(
            skip_id=str(skip.id),
            kind=SkipAssetKind.labels_pdf,
            idx=None,
            content_type="application/pdf",
            data=pdf_bytes,
        )
    )

    await session.commit()

    return SkipOut(
        id=skip.id,
        qr_code=qr_code,
        owner_org_id=skip.owner_org_id,  # str → parsed by Pydantic
        labels_pdf_url=f"/skips/{skip.id}/labels.pdf",
        label_png_urls=[f"/skips/{skip.id}/labels/{i}.png" for i in range(1, 4)],
    )


@router.get("/{skip_id}/labels.pdf")
async def get_skip_labels_pdf(
    skip_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: Any = Depends(get_current_user),
):
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")

    asset = (
        await session.execute(
            select(SkipAsset).where(
                SkipAsset.skip_id == str(skip_id),
                SkipAsset.kind == SkipAssetKind.labels_pdf,
            )
        )
    ).scalars().first()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Labels PDF not found")

    return StreamingResponse(iter([asset.data]), media_type=asset.content_type)


@router.get("/{skip_id}/labels/{idx}.png")
async def get_skip_label_png(
    skip_id: uuid.UUID,
    idx: int,
    session: AsyncSession = Depends(get_session),
    user: Any = Depends(get_current_user),
):
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")

    asset = (
        await session.execute(
            select(SkipAsset).where(
                SkipAsset.skip_id == str(skip_id),
                SkipAsset.kind == SkipAssetKind.label_png,
                SkipAsset.idx == idx,
            )
        )
    ).scalars().first()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Label PNG not found")

    return StreamingResponse(iter([asset.data]), media_type=asset.content_type)
