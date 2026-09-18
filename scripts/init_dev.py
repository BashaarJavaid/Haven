"""Provision the local demo infrastructure, never household device actions."""

import asyncio
import json
import os
import secrets
import socket
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values, set_key
from websockets.asyncio.client import connect

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
HA_URL = "http://127.0.0.1:8123"
DEADLINE = 180
POLL = 2
REQUEST_TIMEOUT = 10
# Unmodified entity IDs verified against HA 2026.9.2's demo platforms:
# https://github.com/home-assistant/core/tree/2026.9.2/homeassistant/components/demo
DEMO_ENTITIES = {
    "light.bed_light",
    "climate.ecobee",
    "cover.garage_door",
    "sensor.outside_temperature",
}
RECOVERY = (
    "HA is already onboarded without a usable saved token. Sign in at "
    "http://localhost:8123, finish any pending onboarding, create a long-lived "
    "token under Profile > Security, save it as HA_TOKEN in .env, and rerun. "
    "Do not delete volumes to recover credentials."
)


class DevError(Exception):
    """An actionable message safe to print (never include upstream bodies)."""


def read_env() -> dict[str, str]:
    if ENV_FILE.is_symlink():
        raise DevError(".env must be a regular file, not a symlink.")
    return {k: v for k, v in dotenv_values(ENV_FILE, interpolate=False).items() if v}


def prepare_env(existing_volumes: set[str]) -> dict[str, str]:
    values = read_env()
    for volume, keys in {
        "postgres": ("POSTGRES_PASSWORD",),
        "homeassistant": ("HA_USERNAME", "HA_PASSWORD"),
    }.items():
        if volume in existing_volumes and any(not values.get(key) for key in keys):
            raise DevError(
                f"Existing {volume} volume has missing .env credentials; "
                "restore the original .env before initializing. Data was not reset."
            )
    # Exclusive creation avoids replacing an existing file. set_key preserves
    # unrelated entries and uses an atomic replacement; never shell-source .env.
    if not ENV_FILE.exists():
        with open(ENV_FILE, "x", opener=lambda p, f: os.open(p, f, 0o600)) as file:
            file.write((ROOT / ".env.example").read_text())
    ENV_FILE.chmod(0o600)
    for key in ("POSTGRES_PASSWORD", "HA_USERNAME", "HA_PASSWORD"):
        if not values.get(key):
            values[key] = "hirz" if key == "HA_USERNAME" else secrets.token_urlsafe(32)
            set_key(ENV_FILE, key, values[key])
    ENV_FILE.chmod(0o600)
    return values


async def command(*args: str, stdin: bytes | None = None) -> str:
    # Compose and checks use .env as their credential source even if the shell
    # has conflicting values. No credential appears in command-line arguments.
    env = dict(os.environ)
    values = read_env()
    env.update(
        {
            key: values.get(key, "")
            for key in ("POSTGRES_PASSWORD", "HA_USERNAME", "HA_PASSWORD", "HA_TOKEN")
        }
    )
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=ROOT,
            env=env,
            stdin=asyncio.subprocess.PIPE if stdin is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate(stdin)
    except FileNotFoundError:
        raise DevError("Docker is missing. Install and start Docker Desktop.") from None
    if process.returncode:
        raise DevError(
            "Docker command failed. Check that Docker is running, images are "
            "reachable, and ports are free; inspect Compose service status. "
            "Captured output is withheld because it may contain credentials."
        )
    return stdout.decode()


def project() -> str:
    return os.environ.get("COMPOSE_PROJECT_NAME", "hirz")


async def compose(*args: str, stdin: bytes | None = None) -> str:
    return await command(
        "docker",
        "compose",
        "--project-name",
        project(),
        "--env-file",
        str(ENV_FILE),
        "-f",
        str(ROOT / "compose.dev.yml"),
        *args,
        stdin=stdin,
    )


async def preflight() -> set[str]:
    await command("docker", "info", "--format", "{{.ServerVersion}}")
    label = f"label=com.docker.compose.project={project()}"
    running = set(
        (
            await command(
                "docker",
                "ps",
                "--filter",
                label,
                "--format",
                '{{.Label "com.docker.compose.service"}}',
            )
        ).splitlines()
    )
    for service, port in {
        "postgres": 5432,
        "homeassistant": 8123,
        "hirz": 8000,
        "jaeger": 16686,
    }.items():
        if service in running:
            continue
        with socket.socket() as probe:
            # Like the servers, allow reuse after shutdown (TIME_WAIT), while
            # still rejecting an active listener on the port.
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise DevError(
                    f"Local port {port} is occupied; free it first."
                ) from None
    return set(
        (
            await command(
                "docker",
                "volume",
                "ls",
                "--filter",
                label,
                "--format",
                '{{.Label "com.docker.compose.volume"}}',
            )
        ).splitlines()
    )


def response_json(response: httpx.Response) -> Any:
    if not response.is_success:
        raise DevError(f"HA request failed with HTTP {response.status_code}.")
    try:
        return response.json()
    except ValueError:
        raise DevError("HA returned malformed JSON.") from None


def string_field(data: Any, key: str) -> str:
    if (
        not isinstance(data, dict)
        or not isinstance(data.get(key), str)
        or not data[key]
    ):
        raise DevError("HA returned an unexpected authentication response.")
    return str(data[key])


async def wait_http(client: httpx.AsyncClient) -> None:
    async with asyncio.timeout(DEADLINE):
        while True:
            try:
                response = await client.get(HA_URL + "/", follow_redirects=True)
                if response.status_code == 200:
                    return
            except httpx.TransportError:
                pass
            await asyncio.sleep(POLL)


async def demo_entities(client: httpx.AsyncClient, token: str) -> list[str]:
    async with asyncio.timeout(DEADLINE):
        while True:
            response = await client.get(
                HA_URL + "/api/states", headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 401:
                raise DevError(RECOVERY)
            data = response_json(response)
            if not isinstance(data, list) or any(
                not isinstance(row, dict) or not isinstance(row.get("entity_id"), str)
                for row in data
            ):
                raise DevError("HA returned malformed entity states.")
            entities = [row["entity_id"] for row in data]
            if DEMO_ENTITIES <= set(entities):
                return sorted(entities)
            await asyncio.sleep(POLL)


async def long_lived_token(access_token: str) -> str:
    # https://developers.home-assistant.io/docs/auth_api/#long-lived-access-token
    async with asyncio.timeout(REQUEST_TIMEOUT):
        async with connect(HA_URL.replace("http:", "ws:") + "/api/websocket") as ws:
            greeting = json.loads(await ws.recv())
            if (
                not isinstance(greeting, dict)
                or greeting.get("type") != "auth_required"
            ):
                raise DevError("Unexpected HA WebSocket authentication greeting.")
            await ws.send(json.dumps({"type": "auth", "access_token": access_token}))
            auth = json.loads(await ws.recv())
            if not isinstance(auth, dict) or auth.get("type") != "auth_ok":
                raise DevError("HA WebSocket authentication failed.")
            await ws.send(
                json.dumps(
                    {
                        "id": 1,
                        "type": "auth/long_lived_access_token",
                        "client_name": "Hirz local development",
                        "lifespan": 365,
                    }
                )
            )
            result = json.loads(await ws.recv())
            if (
                not isinstance(result, dict)
                or result.get("id") != 1
                or result.get("type") != "result"
                or result.get("success") is not True
            ):
                raise DevError("HA refused to provision a long-lived token.")
            return string_field(result, "result")


async def provision(client: httpx.AsyncClient, values: dict[str, str]) -> None:
    if token := values.get("HA_TOKEN"):
        await demo_entities(client, token)
        print("PASS HA: reused saved token; real API, demo devices (simulated).")
        return
    response = await client.get(HA_URL + "/api/onboarding")
    if response.status_code == 404:
        raise DevError(RECOVERY)
    steps = response_json(response)
    if (
        not isinstance(steps, list)
        or not steps
        or any(
            not isinstance(step, dict)
            or not isinstance(step.get("step"), str)
            or not isinstance(step.get("done"), bool)
            for step in steps
        )
    ):
        raise DevError("HA returned malformed onboarding state.")
    if any(step["done"] for step in steps):
        raise DevError(RECOVERY)
    # Private onboarding contract pinned with the image; do not edit .storage.
    # https://github.com/home-assistant/core/blob/2026.9.2/homeassistant/components/onboarding/views.py
    code = string_field(
        response_json(
            await client.post(
                HA_URL + "/api/onboarding/users",
                json={
                    "name": "Hirz Developer",
                    "username": values["HA_USERNAME"],
                    "password": values["HA_PASSWORD"],
                    "client_id": HA_URL + "/",
                    "language": "en",
                },
            )
        ),
        "auth_code",
    )
    tokens = response_json(
        await client.post(
            HA_URL + "/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": HA_URL + "/",
            },
        )
    )
    access = string_field(tokens, "access_token")
    refresh = string_field(tokens, "refresh_token")
    headers = {"Authorization": f"Bearer {access}"}
    for step in ("core_config", "analytics", "integration"):
        response_json(
            await client.post(
                HA_URL + "/api/onboarding/" + step,
                headers=headers,
                json={"client_id": HA_URL + "/", "redirect_uri": HA_URL + "/"}
                if step == "integration"
                else {},
            )
        )
    token = await long_lived_token(access)
    set_key(ENV_FILE, "HA_TOKEN", token)
    ENV_FILE.chmod(0o600)
    # Revoke the temporary session; the long-lived token has its own record.
    # https://developers.home-assistant.io/docs/auth_api/#revoking-a-refresh-token
    response = await client.post(HA_URL + "/auth/revoke", data={"token": refresh})
    if response.status_code != 200:
        raise DevError("HA temporary-session revocation failed; saved token retained.")
    await demo_entities(client, token)
    print("PASS HA: token provisioned; real API, demo devices (simulated).")


async def check_postgres() -> None:
    password = read_env().get("POSTGRES_PASSWORD")
    if not password:
        raise DevError("POSTGRES_PASSWORD is missing; restore .env.")
    # Use the network address, not the trusted Unix socket/loopback. Feed the password
    # through stdin so neither argv nor Docker's exec environment records it.
    try:
        result = await compose(
            "exec",
            "-T",
            "postgres",
            "sh",
            "-c",
            "IFS= read -r PGPASSWORD; export PGPASSWORD; "
            'exec psql -h postgres -U hirz -d hirz -Atc "SELECT 1"',
            stdin=(password + "\n").encode(),
        )
    except DevError:
        raise DevError(
            "Postgres authentication/query failed. Check the service status and "
            "restore the original POSTGRES_PASSWORD for an existing volume. "
            "Data was not reset."
        ) from None
    if result.strip() != "1":
        raise DevError("Postgres did not return the expected query result.")
    print("PASS Postgres: authenticated SELECT 1.")


async def main() -> None:
    volumes = await preflight()
    values = prepare_env(volumes)
    print(
        "Starting PostgreSQL and Home Assistant (initial image downloads may take time)."
    )
    await compose(
        "up",
        "-d",
        "--wait",
        "--wait-timeout",
        str(DEADLINE),
        "postgres",
        "homeassistant",
    )
    await check_postgres()
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, trust_env=False) as client:
        await wait_http(client)
        await provision(client, values)
    print("Initialization complete. Run docker compose -f compose.dev.yml up -d.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except DevError as exc:
        sys.exit(f"FAIL: {exc}")
    except (TimeoutError, httpx.HTTPError):
        sys.exit(
            "FAIL: service request/readiness timed out or failed; rerun after checking services."
        )
    except Exception:
        # Authentication libraries may embed payloads in exceptions; no traceback.
        sys.exit(
            "FAIL: initialization failed; credentials and data retained. See README recovery steps."
        )
