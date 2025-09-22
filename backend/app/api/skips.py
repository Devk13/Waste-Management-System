# path: backend/app/api/skips.py
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
from sqlalchemy import select, insert, or_
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

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
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
    """Accept header OR query (?key=...) so links open in a new tab."""
    expected = _admin_key_expected()
    if expected and (x_api_key == expected or key == expected):
        return
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

def _asset_blob_and_ct(a):
    blob = getattr(a, "data", None) or getattr(a, "bytes", None)
    ct = getattr(a, "content_type", None) or getattr(a, "mime", "application/octet-stream")
    return blob, ct

def _kind_value(v) -> str:
    if hasattr(v, "value"):
        return str(v.value)
    if isinstance(v, str):
        return v
    return str(v)

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
    Insert into skip_assets (id set explicitly if present).
    Supports: data/bytes and content_type/mime; stores normalized kind.
    """
    tbl = SkipAsset.__table__  # type: ignore[attr-defined]
    cols = tbl.c

    values: dict[str, object] = {}

    # explicit primary key if present
    if "id" in cols.keys():
        values["id"] = str(uuid.uuid4())

    values["skip_id"] = str(skip_id)
    values["kind"] = _kind_value(kind)
    if "idx" in cols.keys():
        values["idx"] = idx

    if "content_type" in cols.keys():
        values["content_type"] = content_type
    elif "mime" in cols.keys():
        values["mime"] = content_type

    if "data" in cols.keys():
        values["data"] = blob
    elif "bytes" in cols.keys():
        values["bytes"] = blob
    else:
        raise RuntimeError("skip_assets table has neither 'data' nor 'bytes' column")

    await session.execute(insert(tbl).values(**values))

async def _ensure_label_assets(session: AsyncSession, skip: Skip, org_name: str) -> None:
    """Create PNG+PDF assets if they don't exist yet (idempotent)."""
    # already has a PDF?
    existing_pdf = (
        await session.execute(
            select(SkipAsset).where(
                SkipAsset.skip_id == str(skip.id),
                or_(
                    SkipAsset.kind == _kind_value(SkipAssetKind.labels_pdf),
                    getattr(SkipAsset, "content_type", None) == "application/pdf"
                    if hasattr(SkipAsset, "content_type") else False,
                    getattr(SkipAsset, "mime", None) == "application/pdf"
                    if hasattr(SkipAsset, "mime") else False,
                ),
            )
        )
    ).scalar_one_or_none()
    if existing_pdf:
        return

    deeplink = _qr_deeplink(skip.qr_code)
    png_bytes = make_qr_png(deeplink)
    meta = LabelMeta(qr_text=deeplink, qr_code=skip.qr_code, org_name=org_name)
    pdf_bytes = make_three_up_pdf(meta, png_bytes)

    # 3 PNGs
    for i in range(1, 4):
        await _insert_asset_row(
            session,
            skip_id=str(skip.id),
            kind=SkipAssetKind.label_png,   # <- PNG kind
            idx=i,
            content_type="image/png",
            blob=png_bytes,
        )

    # 1 PDF
    await _insert_asset_row(
        session,
        skip_id=str(skip.id),
        kind=SkipAssetKind.labels_pdf,     # <- PDF kind
        idx=None,
        content_type="application/pdf",
        blob=pdf_bytes,
    )

    await session.flush()

# -----------------------------------------------------------------------------
# DEV seed endpoint (guarded) — creates label assets too
# -----------------------------------------------------------------------------
class SeedIn(BaseModel):
    owner_org_id: str | None = None
    owner_org_name: str | None = None
    qr_code: str | None = None
    qr: str | None = None
    size: str | int | None = None
    color: str | None = None
    notes: str | None = None

@router.post("/_seed", status_code=201, tags=["dev"])
async def seed_skip(
    body: SeedIn,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(_admin_key_ok),  # X-API-Key guard
):
    qr = (body.qr_code or body.qr or "").strip()
    if not qr:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"fields": {"qr_code": "Field required"}},
        )

    # resolve org (optional)
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
        org_name = body.owner_org_name

    # idempotent by qr_code — ensure assets if found
    existing = (
        await session.execute(select(Skip).where(Skip.qr_code == qr))
    ).scalar_one_or_none()
    if existing:
        await _ensure_label_assets(session, existing, org_name)
        await session.commit()
        return {"id": str(existing.id), "qr_code": existing.qr_code}

    # create skip
    sk = Skip()
    if hasattr(Skip, "qr_code"):
        sk.qr_code = qr
    if owner_id and hasattr(Skip, "owner_org_id"):
        sk.owner_org_id = owner_id
    if body.color and hasattr(Skip, "color"):
        sk.color = body.color
    if body.notes and hasattr(Skip, "notes"):
        sk.notes = body.notes

    size_val = _to_int(body.size)
    if size_val is not None:
        for col in ("size_m3", "capacity_m3", "size", "wheelie_l", "capacity_l", "rolloff_yd"):
            if hasattr(Skip, col):
                setattr(sk, col, size_val)
                break

    session.add(sk)
    try:
        await session.flush()
        await _ensure_label_assets(session, sk, org_name)
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="seed_failed")

    return {"id": str(getattr(sk, "id", "")), "qr_code": getattr(sk, "qr_code", qr)}

# -----------------------------------------------------------------------------
# Admin create — also creates label assets
# -----------------------------------------------------------------------------
@router.post("", response_model=SkipOut, status_code=201)
async def create_skip(
    payload: SkipCreate,
    session: AsyncSession = Depends(get_db),
    user: Any = Depends(get_current_user),
):
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")

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

    qr_code = payload.qr_code or ("SK-" + uuid.uuid4().hex[:8].upper())
    exists = (
        await session.execute(select(Skip).where(Skip.qr_code == qr_code))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="qr_code already exists")

    owner_org_id = str(payload.owner_org_id)
    assigned_id = str(payload.assigned_commodity_id) if payload.assigned_commodity_id else None
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

    # labels
    deeplink = _qr_deeplink(qr_code)
    png_bytes = make_qr_png(deeplink)
    meta = LabelMeta(qr_text=deeplink, qr_code=qr_code, org_name=org_name)
    pdf_bytes = make_three_up_pdf(meta, png_bytes)

    for i in range(1, 4):
        await _insert_asset_row(
        session,
        skip_id=str(skip.id),
        kind=_kind_value(SkipAssetKind.label_png),
        idx=i,
        content_type="image/png",
        blob=png_bytes,
    )

    # PDF
    await _insert_asset_row(
        session,
        skip_id=str(skip.id),
        kind=SkipAssetKind.labels_pdf,     # <-- PDF kind
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

# -----------------------------------------------------------------------------
# Labels (PNG/PDF) — allow ?key=...
# -----------------------------------------------------------------------------
@router.get("/{skip_id}/labels.pdf")
async def get_skip_labels_pdf(
    skip_id: str,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(_admin_key_ok_q),  # header OR ?key=
):
    conds = [
        SkipAsset.skip_id == str(skip_id),
    ]
    # match by kind or by content type (handles any past rows with mismatched kind)
    kind_match = (SkipAsset.kind == _kind_value(SkipAssetKind.labels_pdf))
    ct_col = getattr(SkipAsset, "content_type", None)
    mime_col = getattr(SkipAsset, "mime", None)

    type_match = []
    if ct_col is not None:
        type_match.append(SkipAsset.content_type == "application/pdf")
    if mime_col is not None:
        type_match.append(SkipAsset.mime == "application/pdf")

    stmt = select(SkipAsset).where(
        or_(kind_match, *type_match),
        SkipAsset.skip_id == str(skip_id),
    )

    asset = (await session.execute(stmt)).scalar_one_or_none()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Labels PDF not found")

    blob, ct = _asset_blob_and_ct(asset)
    return StreamingResponse(iter([blob]), media_type=ct or "application/pdf")


@router.get("/{skip_id}/labels/{idx}.png")
async def get_skip_label_png(
    skip_id: str,
    idx: int,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(_admin_key_ok_q),  # header OR ?key=
):
    kind_match = (SkipAsset.kind == _kind_value(SkipAssetKind.label_png))
    type_match = []
    if hasattr(SkipAsset, "content_type"):
        type_match.append(SkipAsset.content_type == "image/png")
    if hasattr(SkipAsset, "mime"):
        type_match.append(SkipAsset.mime == "image/png")

    stmt = select(SkipAsset).where(
        SkipAsset.skip_id == str(skip_id),
        SkipAsset.idx == idx,
        or_(kind_match, *type_match),
    )

    asset = (await session.execute(stmt)).scalar_one_or_none()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Label PNG not found")

    blob, ct = _asset_blob_and_ct(asset)
    return StreamingResponse(iter([blob]), media_type=ct or "image/png")

# -----------------------------------------------------------------------------
# Debug: list stored assets for a skip (very helpful for validation)
# -----------------------------------------------------------------------------
@router.get("/{skip_id}/__assets", tags=["dev"])
async def debug_assets(
    skip_id: str,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(_admin_key_ok_q),  # header OR ?key=
):
    rows = await session.execute(select(SkipAsset).where(SkipAsset.skip_id == str(skip_id)))
    out = []
    for a in rows.scalars().all():
        blob, ct = _asset_blob_and_ct(a)
        out.append({
            "id": getattr(a, "id", None),
            "skip_id": getattr(a, "skip_id", None),
            "kind": getattr(a, "kind", None),
            "idx": getattr(a, "idx", None),
            "content_type": ct,
            "bytes": (len(blob) if blob else 0),
        })
    return {"items": out, "count": len(out)}

@router.get("/{skip_id}/assets/_debug")
async def debug_list_assets(
    skip_id: str,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(_admin_key_ok_q),
):
    rows = (await session.execute(
        select(SkipAsset).where(SkipAsset.skip_id == str(skip_id))
    )).scalars().all()

    out = []
    for a in rows:
        blob, ct = _asset_blob_and_ct(a)
        out.append({
            "id": getattr(a, "id", None),
            "skip_id": getattr(a, "skip_id", None),
            "kind": getattr(a, "kind", None),
            "idx": getattr(a, "idx", None),
            "content_type": getattr(a, "content_type", None) or getattr(a, "mime", None),
            "size_bytes": len(blob) if blob else 0,
        })
    return {"assets": out}
