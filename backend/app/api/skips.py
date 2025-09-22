from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Any, Optional
import os                                              
from fastapi import APIRouter, Depends, Header, HTTPException, status       
from pydantic import BaseModel                                              
from sqlalchemy.ext.asyncio import AsyncSession                             
from app.core.config import settings                                       
from app.models.models import Skip
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from app.models import SkipStatus
from app.models import SkipPlacement as DBPlacement
from app.api.deps import get_db

from app.api.deps import get_current_user

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

# ── single, robust guard for seed endpoint ────────────────────────────────────
def _admin_key_ok(
    x_api_key: str | None = Header(None)  # header is "X-Api-Key"
) -> None:
    expected = settings.ADMIN_API_KEY or os.getenv("SEED_API_KEY")

    if not expected or x_api_key != expected:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


class SeedIn(BaseModel):
    # allow either id or plain name for the owner org
    owner_org_id: str | None = None
    owner_org_name: str | None = None

    # accept either qr_code or qr
    qr_code: str | None = None
    qr: str | None = None

    # free-form attributes
    size: str | int | None = None
    color: str | None = None
    notes: str | None = None

def _to_int(v):
    if v is None:
        return None
    try:
        return int(str(v).strip())
    except Exception:
        return None

@router.post("/_seed", status_code=201, tags=["dev"])
async def seed_skip(
    body: SeedIn,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(_admin_key_ok),  # authentication guard (X-API-Key)
):
    # 1) normalize qr
    qr = (body.qr_code or body.qr or "").strip()
    if not qr:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"fields": {"qr_code": "Field required"}})

    # 2) idempotent by qr_code
    existing = (
        await session.execute(select(Skip).where(Skip.qr_code == qr))
    ).scalar_one_or_none()
    if existing:
        return {"id": str(existing.id), "qr_code": existing.qr_code}

    # 3) instantiate without unsupported kwargs, then set attributes that exist
    sk = Skip()
    if hasattr(Skip, "qr_code"):
        sk.qr_code = qr

    # owner org: by id or by name (if Organization available)
    owner_id = (body.owner_org_id or "").strip() or None
    if not owner_id and body.owner_org_name and Organization is not None:
        row = await session.execute(
            select(Organization).where(getattr(Organization, "name") == body.owner_org_name)
        )
        org = row.scalar_one_or_none()
        if not org:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Owner org not found")
        owner_id = getattr(org, "id")

    if owner_id and hasattr(Skip, "owner_org_id"):
        sk.owner_org_id = owner_id

    if body.color and hasattr(Skip, "color"):
        sk.color = body.color
    if body.notes and hasattr(Skip, "notes"):
        sk.notes = body.notes

    # 4) map human "size" to whatever capacity column your model has
    size_val = _to_int(body.size)
    if size_val is not None:
        for col in ("size_m3", "capacity_m3", "size", "wheelie_l", "capacity_l", "rolloff_yd"):
            if hasattr(Skip, col):
                setattr(sk, col, size_val)
                break  # stop at the first match

    # 5) persist
    session.add(sk)
    try:
        await session.flush()
        await session.commit()
    except Exception as e:
        await session.rollback()
        # keep the concise message you already used for smoke test UX
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="seed_failed")

    return {"id": str(getattr(sk, "id", "")), "qr_code": getattr(sk, "qr_code", qr)}


def _qr_deeplink(code: str) -> str:
    base = settings.DRIVER_QR_BASE_URL
    if base:
        return f"{base.rstrip('/')}/driver/qr/{code}"
    return code


@router.post("", response_model=SkipOut, status_code=201)
async def create_skip(
    payload: SkipCreate,
    session: AsyncSession = Depends(get_db),
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
    session: AsyncSession = Depends(get_db),
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
    session: AsyncSession = Depends(get_db),
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
