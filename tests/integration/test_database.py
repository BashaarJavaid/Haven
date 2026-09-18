"""Real PostgreSQL constraints; every test owns and drops a disposable database."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from hirz import db
from hirz.local import LocalError, read_env

pytestmark = pytest.mark.integration


@pytest.fixture
def scratch_database():
    url = db.database_url(read_env(Path(".env")))
    name = "hirz_test_" + uuid4().hex

    async def manage(verb):
        engine = create_async_engine(
            url, isolation_level="AUTOCOMMIT", poolclass=sa.pool.NullPool
        )
        try:
            async with engine.connect() as connection:
                # Name is generated here, never supplied by an external caller.
                await connection.exec_driver_sql(f'{verb} DATABASE "{name}"')
        finally:
            await engine.dispose()

    asyncio.run(manage("CREATE"))
    try:
        yield url.set(database=name)
    finally:
        asyncio.run(manage("DROP"))


@asynccontextmanager
async def connect(url):
    engine = create_async_engine(url, poolclass=sa.pool.NullPool, hide_parameters=True)
    try:
        async with engine.connect() as connection:
            yield connection
    finally:
        await engine.dispose()


async def migrate(connection, direction="upgrade", target="head"):
    def run(sync_connection):
        config = db.migration_config()
        config.attributes["connection"] = sync_connection
        getattr(command, direction)(config, target)

    await connection.run_sync(run)
    await connection.commit()


async def rejected(connection, statement):
    with pytest.raises(sa.exc.IntegrityError):
        async with connection.begin_nested():
            await connection.execute(statement)


async def household(connection):
    household_id = uuid4()
    await connection.execute(
        db.households.insert().values(
            id=household_id,
            name="Schema fixture",
            timezone="America/Chicago",
            locale="en-US",
        )
    )
    return household_id


def test_migration_roundtrip_and_no_seeds(scratch_database):
    async def run():
        async with connect(scratch_database) as connection:
            await connection.run_sync(db.require_empty_audit)
            with pytest.raises(LocalError, match="Migrations"):
                await connection.run_sync(db.require_current)
            await migrate(connection)
            await migrate(connection)
            await connection.run_sync(db.require_current)
            await connection.run_sync(db.require_empty_audit)
            for table in db.metadata.sorted_tables:
                assert (
                    await connection.scalar(
                        sa.select(sa.func.count()).select_from(table)
                    )
                    == 0
                )
            await migrate(connection, "downgrade", "base")
            tables = await connection.run_sync(
                lambda c: sa.inspect(c).get_table_names()
            )
            assert set(tables) == {"alembic_version"}
            await migrate(connection)
            await connection.run_sync(db.require_empty_audit)

    asyncio.run(run())


def test_identity_constraints_and_household_scope(scratch_database):
    async def run():
        async with connect(scratch_database) as connection:
            await migrate(connection)
            first, second = await household(connection), await household(connection)
            member_a, member_b = uuid4(), uuid4()
            for home, member in ((first, member_a), (second, member_b)):
                await connection.execute(
                    db.members.insert().values(
                        household_id=home,
                        id=member,
                        display_name="Schema fixture",
                        role="owner",
                    )
                )
                await connection.execute(
                    db.member_accounts.insert().values(
                        household_id=home,
                        member_id=member,
                        provider="fixture",
                        sub="shared",
                    )
                )
            await rejected(
                connection,
                db.member_accounts.insert().values(
                    household_id=first,
                    member_id=member_a,
                    provider="fixture",
                    sub="shared",
                ),
            )
            await rejected(
                connection,
                db.member_accounts.insert().values(
                    household_id=first,
                    member_id=member_b,
                    provider="fixture",
                    sub="cross-home",
                ),
            )
            await rejected(
                connection,
                db.members.insert().values(
                    household_id=first,
                    id=uuid4(),
                    display_name="Schema fixture",
                    role="admin",
                ),
            )
            for column in ("name", "timezone", "locale"):
                values = dict(
                    id=uuid4(), name="Fixture", timezone="UTC", locale="en-US"
                )
                values[column] = ""
                await rejected(connection, db.households.insert().values(**values))
            for column in ("provider", "sub"):
                values = dict(
                    household_id=first,
                    member_id=member_a,
                    provider="fixture",
                    sub="new",
                )
                values[column] = ""
                await rejected(connection, db.member_accounts.insert().values(**values))
            await rejected(
                connection, db.households.delete().where(db.households.c.id == first)
            )
            await rejected(
                connection,
                db.members.delete().where(db.members.c.household_id == first),
            )

    asyncio.run(run())


def test_audit_constraints_defaults_and_missing_key_refusal(scratch_database):
    async def run():
        async with connect(scratch_database) as connection:
            await migrate(connection)
            first, second = await household(connection), await household(connection)
            for home in (first, second):
                await connection.execute(
                    db.audit_pointer.insert().values(household_id=home)
                )
            pointers = (
                (await connection.execute(sa.select(db.audit_pointer))).mappings().all()
            )
            assert all(
                row["seq"] == 0 and row["curr_hash"] == "0" * 64 for row in pointers
            )
            # Synthetic schema fixture, not a signed event or a household action.
            values = dict(
                household_id=first,
                seq=1,
                event_type="SCHEMA_FIXTURE",
                payload={},
                prev_hash="0" * 64,
                curr_hash="a" * 64,
                key_fingerprint="b" * 64,
                signature=b"schema-only",
            )
            for column, value in (
                ("seq", 0),
                ("seq", -1),
                ("payload", []),
                ("event_type", ""),
                ("signature", b""),
                ("curr_hash", "A" * 64),
                ("prev_hash", "0" * 63),
                ("key_fingerprint", "g" * 64),
            ):
                await rejected(
                    connection,
                    db.audit_log.insert().values(**(values | {column: value})),
                )
            await connection.execute(db.audit_log.insert().values(**values))
            await connection.execute(
                db.audit_log.insert().values(**(values | {"household_id": second}))
            )
            await rejected(connection, db.audit_log.insert().values(**values))
            created = await connection.scalar(
                sa.select(db.audit_log.c.created_at).limit(1)
            )
            assert created.tzinfo is not None
            await rejected(connection, db.audit_pointer.update().values(seq=-1))
            await rejected(
                connection, db.audit_pointer.update().values(curr_hash="bad")
            )
            with pytest.raises(LocalError, match="Audit rows exist"):
                await connection.run_sync(db.require_empty_audit)

    asyncio.run(run())


def test_partial_schema_and_revision_fail_closed(scratch_database):
    async def run():
        async with connect(scratch_database) as connection:
            await connection.exec_driver_sql("CREATE TABLE unrelated (id integer)")
            with pytest.raises(LocalError, match="Migrations"):
                await connection.run_sync(db.require_empty_audit)
            await connection.rollback()
            await migrate(connection)
            async with connection.begin_nested() as transaction:
                await connection.exec_driver_sql("DROP TABLE audit_pointer")
                with pytest.raises(LocalError, match="Migrations"):
                    await connection.run_sync(db.require_current)
                with pytest.raises(LocalError, match="Migrations"):
                    await connection.run_sync(db.require_empty_audit)
                await transaction.rollback()
            async with connection.begin_nested() as transaction:
                await connection.exec_driver_sql(
                    "ALTER TABLE households DROP COLUMN locale"
                )
                with pytest.raises(LocalError, match="Schema is inconsistent"):
                    await connection.run_sync(db.require_empty_audit)
                await transaction.rollback()
            async with connection.begin_nested() as transaction:
                await connection.exec_driver_sql(
                    "UPDATE alembic_version SET version_num = 'unknown'"
                )
                with pytest.raises(LocalError, match="Migrations"):
                    await connection.run_sync(db.require_current)
                await transaction.rollback()

    asyncio.run(run())
