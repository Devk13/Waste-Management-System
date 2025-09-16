# path: alembic/env.py
from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Sequence, Union

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# --- ensure `backend/` (this file's grandparent) is on sys.path so `import app.*` works
import sys, pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ------------------------------------------------------------
# Alembic Config
# ------------------------------------------------------------
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------
# Load app metadata & DB URL
# ------------------------------------------------------------
# We import the app's DB normalizer and models so autogenerate can see them.
from app.db import DB_URL  # type: ignore

# Import models to register tables with SQLAlchemy's registry
from app.models.skip import Base as SkipBase  # type: ignore
from app.models.labels import Base as LabelsBase  # type: ignore
from app.models.driver import Base as DriverBase  # type: ignore

from sqlalchemy import MetaData


def _combine_metadata(*metas: Sequence[MetaData]) -> MetaData:
    combined = MetaData()
    for m in metas:
        for t in m.tables.values():
            t.tometadata(combined)
    return combined

# All tables across model groups
target_metadata = _combine_metadata(
    SkipBase.metadata,
    LabelsBase.metadata,
    DriverBase.metadata,
)

# Ensure Alembic uses the app's DB URL (Render et al.)
config.set_main_option("sqlalchemy.url", DB_URL)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable: Union[AsyncEngine, Connection]

    # Use async engine for async drivers (postgresql+asyncpg / sqlite+aiosqlite)
    if DB_URL.startswith("postgresql+") or DB_URL.startswith("sqlite+"):
        connectable = create_async_engine(DB_URL, poolclass=pool.NullPool)

        async def _run_async_migrations() -> None:
            async with connectable.connect() as connection:  # type: ignore[assignment]
                await connection.run_sync(do_run_migrations)

        asyncio.run(_run_async_migrations())
    else:
        # Fallback to sync engine if a sync driver is used
        config_section = config.get_section(config.config_ini_section) or {}
        config_section["sqlalchemy.url"] = DB_URL
        connectable = engine_from_config(
            config_section,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:  # type: ignore[assignment]
            do_run_migrations(connection)


# Entrypoint
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
