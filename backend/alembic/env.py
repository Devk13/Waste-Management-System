import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1) Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# 2) Alembic Config object
config = context.config

# Inject DATABASE_URL from environment into alembic.ini at runtime
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3) Metadata for autogenerate (optional). If you have a Base, import it.
# from backend.app.models.base import Base  # if you have a Base class
target_metadata = None  # set to Base.metadata if you want autogenerate

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Detect async driver (e.g., sqlite+aiosqlite, postgresql+asyncpg)
    url = config.get_main_option("sqlalchemy.url")
    if url and ("+asyncpg" in url or "+aiosqlite" in url):
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()
    else:
        # Fallback: sync engine (e.g., sqlite:/// or postgresql://)
        connectable = create_engine(url, poolclass=pool.NullPool)
        with connectable.connect() as connection:
            do_run_migrations(connection)
        connectable.dispose()

def run_migrations():
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())

if __name__ == "__main__":
    run_migrations()
