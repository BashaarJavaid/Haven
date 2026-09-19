"""Internal API smoke in a disposable database; never operates a device."""

import asyncio
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from hirz import db
from hirz.constitution.boundary import Dogwood
from hirz.constitution.schema import Constitution, load
from hirz.graph.models import now
from hirz.graph.seeds import demo_id, load_seeds, read_seed
from hirz.local import read_env, signing_key
from hirz.pipeline.audit import AuditWriter
from hirz.pipeline.hashing import action_hash
from hirz.pipeline.models import Action, Principal
from hirz.pipeline.service import Pipeline, PolicyBundle


async def main() -> None:
    values = read_env(Path(".env"))
    url = db.database_url(values)
    name = "hirz_smoke_" + uuid4().hex
    admin = create_async_engine(
        url,
        isolation_level="AUTOCOMMIT",
        poolclass=sa.pool.NullPool,
        hide_parameters=True,
    )
    engine = create_async_engine(
        url.set(database=name), poolclass=sa.pool.NullPool, hide_parameters=True
    )
    created = False
    try:
        async with admin.connect() as connection:
            await connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
            created = True
        async with engine.connect() as connection:

            def migrate(sync: sa.Connection) -> None:
                config = db.migration_config()
                config.attributes["connection"] = sync
                command.upgrade(config, "head")

            await connection.run_sync(migrate)
            await connection.commit()
            seed = read_seed(Path("constitutions/quinn-home.yaml"))
            at = now()
            await load_seeds(connection, [seed], lambda: at)
            policy_data = load(Path("constitutions/quinn-home.yaml")).model_dump()
            policy_data["autonomy"]["communication"]["notify_member"].update(
                mode="ask", budget={"usd_per_day": "1"}
            )
            boundary = Dogwood()
            bundle = await PolicyBundle.validate(
                seed.household_id, Constitution.model_validate(policy_data), boundary
            )
            pipeline = Pipeline(
                connection,
                bundle,
                boundary,
                AuditWriter(signing_key(values)),
                lambda: at + timedelta(seconds=1),
            )
            principal = Principal(provider="demo", sub="malik", surface="app")
            action = Action.model_validate(
                {
                    "action_id": "act_" + uuid4().hex,
                    "class": "communication.notify_member",
                    "target": {
                        "adapter": "member",
                        "entity": str(demo_id("quinn-home", "members", "mom")),
                    },
                    "params": {},
                    "requested_by": {
                        "member_id": None,
                        "role": "unknown",
                        "surface": "app",
                    },
                    "reason": "Synthetic internal authorization smoke",
                    "content_hash": "",
                }
            )
            action = action.model_copy(update={"content_hash": action_hash(action)})
            preview = await pipeline.evaluate(action, principal, cost=Decimal("0.25"))
            assert preview.event_type == "ASK_CONSTITUTION" and preview.audit_id is None
            proposed = await pipeline.propose(action, principal, cost=Decimal("0.25"))
            assert proposed.approval is not None
            voted = await pipeline.vote(
                proposed.approval.approval_id, principal, approved=True
            )
            grant = await pipeline.redeem(
                action,
                principal,
                cost=Decimal("0.25"),
                approval_id=proposed.approval.approval_id,
            )
            replay = await pipeline.redeem(
                action,
                principal,
                cost=Decimal("0.25"),
                approval_id=proposed.approval.approval_id,
            )
            assert (
                grant.event_type == "EXECUTE"
                and replay.event_type == "DENY_APPROVAL_USED"
            )
            assert grant.budget and grant.budget.reserved == Decimal("0.25")
            print(f"evaluate={preview.event_type} audit=None")
            print(f"propose={proposed.event_type}; vote={voted.event_type}")
            print(
                f"redeem={grant.event_type}; boundary={grant.boundary.engine}; reserved={grant.budget.reserved}"
            )
            print(
                f"replay={replay.event_type}; committed_grants=1; device_operations=0"
            )
            stored = await connection.scalar(
                sa.select(db.constitution_versions.c.status)
            )
            print(
                f"stored_seed={stored}; source=twin; public_authentication=not_implemented"
            )
    finally:
        await engine.dispose()
        if created:
            async with admin.connect() as connection:
                await connection.exec_driver_sql(f'DROP DATABASE "{name}"')
        await admin.dispose()


if __name__ == "__main__":
    asyncio.run(main())
