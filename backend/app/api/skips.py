from __future__ import annotations
import uuid
from typing import Any, Optional

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
