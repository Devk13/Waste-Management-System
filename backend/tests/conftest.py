import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.main import app as fastapi_app
from app.db import Base, get_session

# Ensure models are registered on metadata
import importlib
importlib.import_module("app.models.skip")
importlib.import_module("app.models.labels")

# Ensure /skips router is mounted for tests
try:
    from app.api.skips import router as skips_router
    if not any("/skips" in getattr(r, "path", "") for r in fastapi_app.router.routes):
        fastapi_app.include_router(skips_router)
except Exception:
    pass

TEST_DB = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def engine_fixture():
    engine = create_async_engine(TEST_DB, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()

@pytest_asyncio.fixture
async def session(engine_fixture) -> AsyncGenerator[AsyncSession, None]:
    SessionLocal = async_sessionmaker(engine_fixture, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as s:
        yield s

@pytest_asyncio.fixture
async def client(engine_fixture) -> AsyncGenerator[AsyncClient, None]:
    SessionLocal = async_sessionmaker(engine_fixture, expire_on_commit=False, class_=AsyncSession)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with SessionLocal() as s:
            yield s

    fastapi_app.dependency_overrides[get_session] = override_get_session

    # httpx>=0.24 removed AsyncClient(app=...). Use ASGITransport instead.
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    fastapi_app.dependency_overrides.clear()

@pytest.fixture
def seeded():
    from app.models import models as m
    return {
        "users": {
            "admin": m.User(id=str(uuid.uuid4()), role=m.UserRole.admin),
            "driver": m.User(id=str(uuid.uuid4()), role=m.UserRole.driver),
        },
        "orgs": {
            "default": type("Org", (), {"id": uuid.uuid4(), "name": "OWNER"})(),
        },
    }
