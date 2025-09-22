# backend/app/api/skips.py
from __future__ import annotations

import os
import uuid
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.deps import get_db, get_current_user
from app.models.models import Skip
from app.models.labels import SkipAsset, SkipAssetKind
from app.schemas.skip import SkipCreate, SkipOut
from app.services.qr_labels import LabelMeta, make_qr_png, make_three_up_pdf

# Optional Organization model (skip gracefully if not present)
try:
    from app.models.organization import Organization  # type: ignore
except Exception:  # pragma: no cover
    Organization = None  # type: ignore

router = APIRouter(prefix="/skips", tags=["skips"])

# --- helpers for SkipAsset variations ----------------------------------------
def _new_asset(*, skip_id: str, kind: int | str, idx: int | None,
               content_type: str, blob: bytes) -> SkipAsset:
    """
    Create a SkipAsset instance that works with different model shapes:
    - id column present and NOT NULL -> set it explicitly
    - binary column may be 'data' or 'bytes'
    - content-type column may be 'content_type' or 'mime'
    """
    fields: dict[str, object] = {}

    # required columns
    fields["skip_id"] = str(skip_id)
    fields["kind"] = kind
    if hasattr(SkipAsset, "idx"):
        fields["idx"] = idx

    # explicit id if there's a NOT NULL id column with no default
    if hasattr(SkipAsset, "id"):
        fields["id"] = str(uuid.uuid4())

    # choose the right binary column name
    bin_attr = "data" if hasattr(SkipAsset, "data") else ("bytes" if hasattr(SkipAsset, "bytes") else None)
    if not bin_attr:
        raise RuntimeError("SkipAsset model has neither 'data' nor 'bytes' column")
    fields[bin_attr] = blob

    # choose the right content type column name
    ct_attr = "content_type" if hasattr(SkipAsset, "content_type") else ("mime" if hasattr(SkipAsset, "mime") else None)
    if ct_attr:
        fields[ct_attr] = content_type

    return SkipAsset(**fields)  # type: ignore[arg-type]

async def _insert_asset_row(
    session: AsyncSession,
    *,
    skip_id: str,
    kind: int | str,
    idx: int | None,
    content_type: str,
    blob: bytes,
) -> None:
    """Insert into skip_assets using Core and set id explicitly if the table has it."""
    tbl = SkipAsset.__table__  # type: ignore[attr-defined]
    cols = tbl.c

    values: dict[str, object] = {}

    # explicit primary key if present and non-nullable
    if "id" in cols.keys():
        values["id"] = str(uuid.uuid4())

    # required / common columns
    values["skip_id"] = str(skip_id)
    values["kind"] = kind
    if "idx" in cols.keys():
        values["idx"] = idx

    # choose content-type column
    if "content_type" in cols.keys():
        values["content_type"] = content_type
    elif "mime" in cols.keys():
        values["mime"] = content_type

    # choose binary column
    if "data" in cols.keys():
        values["data"] = blob
    elif "bytes" in cols.keys():
        values["bytes"] = blob
    else:
        raise RuntimeError("skip_assets table has neither 'data' nor 'bytes' column")

    await session.execute(insert(tbl).values(**values))

# Auth helpers
def _admin_key_expected() -> Optional[str]:
    # Support either ADMIN_API_KEY or legacy SEED_API_KEY
    return getattr(settings, "ADMIN_API_KEY", None) or os.getenv("SEED_API_KEY")


def _admin_key_ok(x_api_key: str | None = Header(None, alias="X-API-Key")) -> None:
    expected = _admin_key_expected()
    if not expected or x_api_key != expected:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def _admin_key_ok_q(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    key: str | None = Query(None),
) -> None:
    """
    Accept admin key from header OR from query string (?key=...),
    so new-tab links can work without custom headers.
    """
    expected = _admin_key_expected()
    if expected and (x_api_key == expected or key == expected):
        return
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _qr_deeplink(code: str) -> str:
    base = getattr(settings, "DRIVER_QR_BASE_URL", "")
    if base:
        return f"{base.rstrip('/')}/driver/qr/{code}"
    return code


def _to_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(str(v).strip())
    except Exception:
        return None


async def _ensure_label_assets(session: AsyncSession, skip: Skip, org_name: str) -> None:
    """Create PNG+PDF assets if they don't exist yet."""
    # Any labels PDF already?
    existing_pdf = (
        await session.execute(
            select(SkipAsset).where(
                SkipAsset.skip_id == str(skip.id),
                SkipAsset.kind == SkipAssetKind.labels_pdf,
            )
        )
    ).scalar_one_or_none()
    if existing_pdf:
        return

    deeplink = _qr_deeplink(skip.qr_code)
    png_bytes = make_qr_png(deeplink)
    meta = LabelMeta(qr_text=deeplink, qr_code=skip.qr_code, org_name=org_name)
    pdf_bytes = make_three_up_pdf(meta, png_bytes)

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
    await session.flush()

async def _insert_asset_row(
    session: AsyncSession,
    *,
    skip_id: str,
    kind: int | str,
    idx: int | None,
    content_type: str,
    blob: bytes,
) -> None:
    """
    Insert into skip_assets using Core and set `id` explicitly if the table has it.
    Handles schema variants: content_type/mime and data/bytes.
    """
    tbl = SkipAsset.__table__  # type: ignore[attr-defined]
    cols = tbl.c

    values: dict[str, object] = {}

    # explicit primary key if present (avoids NOT NULL on id)
    if "id" in cols.keys():
        values["id"] = str(uuid.uuid4())

    values["skip_id"] = str(skip_id)
    values["kind"] = kind
    if "idx" in cols.keys():
        values["idx"] = idx

    # content-type column name may vary
    if "content_type" in cols.keys():
        values["content_type"] = content_type
    elif "mime" in cols.keys():
        values["mime"] = content_type

    # binary payload column name may vary
    if "data" in cols.keys():
        values["data"] = blob
    elif "bytes" in cols.keys():
        values["bytes"] = blob
    else:
        raise RuntimeError("skip_assets table has neither 'data' nor 'bytes' column")

    await session.execute(insert(tbl).values(**values))

# ──────────────────────────────────────────────────────────────────────────────
# DEV seed endpoint (guarded) — now creates label assets too
# ──────────────────────────────────────────────────────────────────────────────
class SeedIn(BaseModel):
    # owner org by id or by name
    owner_org_id: str | None = None
    owner_org_name: str | None = None

    # accept either qr_code or qr
    qr_code: str | None = None
    qr: str | None = None

    # free-form attributes
    size: str | int | None = None
    color: str | None = None
    notes: str | None = None


@router.post("/_seed", status_code=201, tags=["dev"])
async def seed_skip(
    body: SeedIn,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(_admin_key_ok),  # authentication guard (X-API-Key)
):
    # 1) normalize qr
    qr = (body.qr_code or body.qr or "").strip()
    if not qr:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"fields": {"qr_code": "Field required"}},
        )

    # 2) resolve org (optional)
    owner_id: Optional[str] = (body.owner_org_id or "").strip() or None
    org_name = "OWNER"
    if not owner_id and body.owner_org_name and Organization is not None:
        row = await session.execute(
            select(Organization).where(getattr(Organization, "name") == body.owner_org_name)
        )
        org = row.scalar_one_or_none()
        if not org:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Owner org not found")
        owner_id = str(getattr(org, "id"))
        org_name = getattr(org, "name", org_name)
    elif body.owner_org_name:
        # no Organization model, but we still want a nice label
        org_name = body.owner_org_name

    # 3) idempotent by qr_code — and ensure assets if missing
    existing = (
        await session.execute(select(Skip).where(Skip.qr_code == qr))
    ).scalar_one_or_none()
    if existing:
        await _ensure_label_assets(session, existing, org_name)
        await session.commit()
        return {"id": str(existing.id), "qr_code": existing.qr_code}

    # 4) instantiate skip safely
    sk = Skip()
    if hasattr(Skip, "qr_code"):
        sk.qr_code = qr
    if owner_id and hasattr(Skip, "owner_org_id"):
        sk.owner_org_id = owner_id
    if body.color and hasattr(Skip, "color"):
        sk.color = body.color
    if body.notes and hasattr(Skip, "notes"):
        sk.notes = body.notes

    # size/capacity mapping — use the first column that exists
    size_val = _to_int(body.size)
    if size_val is not None:
        for col in ("size_m3", "capacity_m3", "size", "wheelie_l", "capacity_l", "rolloff_yd"):
            if hasattr(Skip, col):
                setattr(sk, col, size_val)
                break

    # 5) persist + assets
    session.add(sk)
    try:
        await session.flush()
        await _ensure_label_assets(session, sk, org_name)
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="seed_failed")

    return {"id": str(getattr(sk, "id", "")), "qr_code": getattr(sk, "qr_code", qr)}


# ──────────────────────────────────────────────────────────────────────────────
# Admin create (unchanged) — also creates label assets
# ──────────────────────────────────────────────────────────────────────────────
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

    # cast UUID-ish fields to str for safety
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

    # Generate assets (3 PNGs + 1 PDF)
    deeplink = _qr_deeplink(qr_code)
    png_bytes = make_qr_png(deeplink)
    meta = LabelMeta(qr_text=deeplink, qr_code=qr_code, org_name=org_name)
    pdf_bytes = make_three_up_pdf(meta, png_bytes)

    # Insert three PNG labels
    for i in range(1, 4):
        await _insert_asset_row(
            session,
            skip_id=str(skip.id),
            kind=SkipAssetKind.label_png,
            idx=i,
            content_type="image/png",
            blob=png_bytes,
        )

    # Insert the 3-up PDF
    await _insert_asset_row(
        session,
        skip_id=str(skip.id),
        kind=SkipAssetKind.labels_pdf,
        idx=None,
        content_type="application/pdf",
        blob=pdf_bytes,
    )

    await session.commit()

    return SkipOut(
        id=skip.id,
        qr_code=qr_code,
        owner_org_id=skip.owner_org_id,
        labels_pdf_url=f"/skips/{skip.id}/labels.pdf",
        label_png_urls=[f"/skips/{skip.id}/labels/{i}.png" for i in range(1, 4)],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Labels (PNG/PDF) — allow ?key=...
# ──────────────────────────────────────────────────────────────────────────────
@router.get("/{skip_id}/labels.pdf")
async def get_skip_labels_pdf(
    skip_id: str,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(_admin_key_ok_q),
):
    asset = (
        await session.execute(
            select(SkipAsset).where(
                SkipAsset.skip_id == str(skip_id),
                SkipAsset.kind == SkipAssetKind.labels_pdf,
            )
        )
    ).scalar_one_or_none()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Labels PDF not found")

    return StreamingResponse(iter([asset.data]), media_type=asset.content_type)


# ---------- label fetchers ----------

@router.get("/{skip_id}/labels.pdf")
async def get_skip_labels_pdf(
    skip_id: str,                              # <- accept string
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

    return StreamingResponse(iter([asset.data if hasattr(asset, "data") else asset.bytes]),
                             media_type=asset.content_type)

@router.get("/{skip_id}/labels/{idx}.png")
async def get_skip_label_png(
    skip_id: str,                              # <- accept string
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

    return StreamingResponse(iter([asset.data if hasattr(asset, "data") else asset.bytes]),
                             media_type=asset.content_type)
