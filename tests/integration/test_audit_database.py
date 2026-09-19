"""Item 10 checks on disposable PostgreSQL, through the real decision pipeline."""

import asyncio
from contextlib import asynccontextmanager

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from test_database import connect, household
from test_database import scratch_database as scratch_database
from test_pipeline_database import NOW, setup

from hirz import db
from hirz.audit import AuditError, verify_database
from hirz.pipeline.service import Pipeline
from tests.unit.test_pipeline import HOME, PRINCIPAL, action

pytestmark = pytest.mark.integration


def test_hundred_concurrent_decisions_and_snapshot(scratch_database, monkeypatch):
    async def run():
        async with connect(scratch_database) as connection:
            pipeline = await setup(connection, native=True)
            key = pipeline.audit.key.public_key()
            engine = create_async_engine(
                scratch_database,
                pool_size=20,
                max_overflow=0,
                pool_timeout=120,
                hide_parameters=True,
            )
            gate = asyncio.Event()

            async def propose():
                await gate.wait()
                async with engine.connect() as other:
                    p = Pipeline(
                        other,
                        pipeline.bundle,
                        pipeline.boundary,
                        pipeline.audit,
                        lambda: NOW,
                    )
                    return await p.propose(action(), PRINCIPAL)

            try:
                tasks = [asyncio.create_task(propose()) for _ in range(100)]
                gate.set()
                decisions = await asyncio.wait_for(asyncio.gather(*tasks), timeout=120)
                assert len({d.audit_id for d in decisions}) == 100
                summary, rows = await verify_database(
                    connection, HOME, key, collect=True
                )
                assert summary["checked_count"] == 100
                assert [row.seq for row in rows] == list(range(1, 101))
                by_seq = {row.seq: row for row in rows}
                for d in decisions:
                    assert by_seq[d.audit_id].payload["action_id"] == d.action_id
                    assert by_seq[d.audit_id].payload["audit_id"] == d.audit_id
                # Force an append after the snapshot/pointer read but before row streaming.
                original = connection.stream

                @asynccontextmanager
                async def stream_after_append(self, *args, **kwargs):
                    assert (
                        await self.scalar(sa.text("SHOW transaction_read_only")) == "on"
                    )
                    assert (
                        await self.scalar(sa.text("SHOW transaction_isolation"))
                        == "repeatable read"
                    )
                    appended = await propose()
                    assert appended.audit_id == 101
                    async with original(*args, **kwargs) as result:
                        yield result

                with monkeypatch.context() as patch:
                    patch.setattr(type(connection), "stream", stream_after_append)
                    snapshot, selected = await verify_database(
                        connection, HOME, key, collect=True, selected=(20, 40)
                    )
                assert snapshot["checked_count"] == 100
                assert [r.seq for r in selected] == list(range(20, 41))
                latest, _ = await verify_database(connection, HOME, key)
                assert latest["checked_count"] == 101
                print(
                    "100 concurrent tasks; connection cap=20; 100 contiguous signed rows; snapshot=100; next snapshot=101"
                )
            finally:
                await engine.dispose()

    asyncio.run(run())


@pytest.mark.parametrize(
    "damage",
    ["payload", "pointer_hash", "pointer_seq", "pointer_missing", "genesis", "gap"],
)
def test_corruption_blocks_verification_and_selected_export(scratch_database, damage):
    async def run():
        async with connect(scratch_database) as connection:
            p = await setup(connection)
            for _ in range(3):
                await p.propose(action(), PRINCIPAL)
            async with connection.begin():
                if damage == "payload":
                    await connection.execute(
                        db.audit_log.update()
                        .where(db.audit_log.c.seq == 3)
                        .values(payload={"mutated": True})
                    )
                elif damage == "pointer_hash":
                    await connection.execute(
                        db.audit_pointer.update().values(curr_hash="f" * 64)
                    )
                elif damage == "pointer_seq":
                    await connection.execute(db.audit_pointer.update().values(seq=2))
                elif damage == "pointer_missing":
                    await connection.execute(db.audit_pointer.delete())
                else:
                    await connection.execute(
                        db.audit_log.delete().where(
                            db.audit_log.c.seq == (1 if damage == "genesis" else 2)
                        )
                    )
            with pytest.raises(AuditError):
                await verify_database(
                    connection,
                    HOME,
                    p.audit.key.public_key(),
                    collect=True,
                    selected=(1, 1),
                )
            assert not connection.in_transaction()

    asyncio.run(run())


def test_empty_unknown_households_ranges_and_read_only(scratch_database):
    async def run():
        async with connect(scratch_database) as connection:
            p = await setup(connection)
            key = p.audit.key.public_key()
            summary, rows = await verify_database(connection, HOME, key, collect=True)
            assert summary["status"] == "empty" and rows == []
            async with connection.begin():
                await connection.execute(
                    db.audit_pointer.insert().values(household_id=HOME)
                )
            assert (await verify_database(connection, HOME, key))[0][
                "status"
            ] == "empty"
            await p.propose(action(), PRINCIPAL)
            async with connection.begin():
                other = await household(connection)
            assert (await verify_database(connection, other, key))[0][
                "checked_count"
            ] == 0
            for selected in ((0, 1), (2, 1), (1, 2)):
                with pytest.raises(AuditError, match="Range"):
                    await verify_database(connection, HOME, key, selected=selected)
            async with connection.begin():
                await connection.execute(
                    db.households.delete().where(db.households.c.id == other)
                )
            with pytest.raises(AuditError, match="Unknown household"):
                await verify_database(connection, other, key)
            async with connection.begin():
                with pytest.raises(AuditError, match="idle"):
                    await verify_database(connection, HOME, key)
            assert (
                await connection.scalar(
                    sa.select(sa.func.count()).select_from(db.audit_log)
                )
                == 1
            )

    asyncio.run(run())
