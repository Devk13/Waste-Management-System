# path: backend/tests/test_skip_labels.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_user
from app.models import models as m
from app.models.labels import SkipAsset, SkipAssetKind

pytestmark = pytest.mark.anyio


async def _as(app, user: m.User):
    async def override():
        return user
    app.dependency_overrides[get_current_user] = override


async def test_create_skip_generates_labels(
    client: AsyncClient, session: AsyncSession, seeded: dict
):
    admin = seeded["users"]["admin"]
    org = seeded["orgs"]["default"]

    await _as(client._transport.app, admin)

    r = await client.post("/skips", json={"owner_org_id": str(org.id)})
    assert r.status_code == 201, r.text
    data = r.json()

    # 3 PNGs + 1 PDF stored
    assets = (
        await session.execute(
            select(SkipAsset).join(m.Skip).where(m.Skip.id == data["id"])
        )
    ).scalars().all()
    kinds = sorted((a.kind, a.idx) for a in assets)

    assert (SkipAssetKind.labels_pdf, None) in kinds
    assert sum(1 for k, _ in kinds if k == SkipAssetKind.label_png) == 3

    # PDF endpoint returns binary
    pdf = await client.get(data["labels_pdf_url"])
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
