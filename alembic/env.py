"""Checkout-only migrations; credentials come from .env, never the command line."""

import asyncio
from pathlib import Path

from alembic.util import CommandError
from sqlalchemy.engine import Connection

from alembic import context
from hirz.db import connect_database, metadata
from hirz.local import LocalError, read_env


def run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=metadata, compare_server_default=True
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    async with connect_database(read_env(Path(".env"))) as connection:
        await connection.run_sync(run_migrations)


try:
    if context.is_offline_mode():
        context.configure(
            dialect_name="postgresql",
            target_metadata=metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
    elif connection := context.config.attributes.get("connection"):
        # Standard Alembic connection sharing, used by isolated integration tests.
        # https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
        run_migrations(connection)
    else:
        asyncio.run(run_online())
except LocalError as exc:
    raise CommandError(str(exc)) from None
except Exception:
    # DB exceptions can contain SQL parameters or connection details.
    raise CommandError(
        "Migration failed; check Postgres, .env, and the migration state. "
        "Credentials and upstream details withheld."
    ) from None
