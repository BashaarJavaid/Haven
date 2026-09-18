"""Read-only local diagnostics. Run from the checkout root."""

import argparse
import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

import httpx
import sqlalchemy as sa

from hirz.db import connect_database, require_current
from hirz.local import (
    DEMO_ENTITIES,
    HA_URL,
    REQUEST_TIMEOUT,
    LocalError,
    read_env,
    signing_key,
)


async def check_postgres(values: dict[str, str]) -> str:
    async with connect_database(values) as connection:
        if await connection.scalar(sa.text("SELECT 1")) != 1:
            raise LocalError("Postgres returned an unexpected query result.")
    return "authenticated SELECT 1."


async def check_ha(values: dict[str, str]) -> str:
    token = values.get("HA_TOKEN")
    if not token:
        raise LocalError("HA_TOKEN is missing; run scripts/init_dev.py.")
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, trust_env=False) as client:
        response = await client.get(
            HA_URL + "/api/states", headers={"Authorization": f"Bearer {token}"}
        )
    if response.status_code != 200:
        raise LocalError("HA state read failed; check the service and saved HA_TOKEN.")
    data = response.json()
    if not isinstance(data, list) or any(
        not isinstance(row, dict) or not isinstance(row.get("entity_id"), str)
        for row in data
    ):
        raise LocalError("HA returned malformed entity states.")
    if not DEMO_ENTITIES <= {row["entity_id"] for row in data}:
        raise LocalError("HA demo entities are missing; check HA initialization.")
    return "real API, demo devices (simulated); required entities present."


async def check_key(values: dict[str, str]) -> str:
    signing_key(values)
    return "P-256 private key signs and verifies an in-memory probe."


async def check_migrations(values: dict[str, str]) -> str:
    async with connect_database(values) as connection:
        await connection.run_sync(require_current)
    return "database matches the sole Alembic head; five tables present."


async def doctor() -> int:
    checks: list[tuple[str, Callable[[dict[str, str]], Awaitable[str]], str]] = [
        ("Postgres", check_postgres, "Check Postgres and restore its .env password."),
        ("HA", check_ha, "Check HA service status and saved HA_TOKEN."),
        ("Signing key", check_key, "Restore the original AUDIT_SIGNING_KEY."),
        (
            "Migrations",
            check_migrations,
            "Check Postgres, then run uv run alembic upgrade head from the checkout root.",
        ),
    ]
    failed = False
    for name, check, recovery in checks:
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                detail = await check(read_env(Path(".env")))
            print(f"PASS {name}: {detail}")
        except LocalError as exc:
            failed = True
            print(f"FAIL {name}: {exc}")
        except Exception:
            failed = True
            print(f"FAIL {name}: check failed or timed out. {recovery}")
    return int(failed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "doctor", help="Check local services, signing key, and migrations"
    )
    parser.parse_args()
    return asyncio.run(doctor())
