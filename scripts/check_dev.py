"""Read-only service checks; --observability also writes one disposable trace."""

import argparse
import asyncio
import json
import secrets
import sys
import time
from pathlib import Path

import httpx

# Support both the documented direct command and imports by pytest.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.init_dev import (  # noqa: E402
    DEADLINE,
    DEMO_ENTITIES,
    HA_URL,
    POLL,
    REQUEST_TIMEOUT,
    DevError,
    check_postgres,
    compose,
    demo_entities,
    read_env,
)


async def check_jaeger(client: httpx.AsyncClient) -> None:
    trace_id = secrets.token_hex(16)
    now = time.time_ns()
    # OTLP/HTTP JSON: hex identifiers, decimal strings for 64-bit timestamps.
    # https://opentelemetry.io/docs/specs/otlp/#json-protobuf-encoding
    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {
                            "key": "service.name",
                            "value": {"stringValue": "hirz-dev-check"},
                        }
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "hirz-dev-check"},
                        "spans": [
                            {
                                "traceId": trace_id,
                                "spanId": secrets.token_hex(8),
                                "name": "disposable-infrastructure-check",
                                "kind": 1,
                                "startTimeUnixNano": str(now),
                                "endTimeUnixNano": str(now + 1_000_000),
                            }
                        ],
                    }
                ],
            }
        ]
    }
    # Use the existing container's stdlib to reach internal OTLP. No SDK or
    # instrumentation is installed in Hirz to produce this disposable probe.
    probe = (
        "import urllib.request\n"
        f"data = {json.dumps(payload).encode()!r}\n"
        "request = urllib.request.Request('http://jaeger:4318/v1/traces', "
        "data=data, headers={'Content-Type': 'application/json'})\n"
        "with urllib.request.urlopen(request, timeout=10) as response:\n"
        "    assert response.status == 200\n"
    )
    async with asyncio.timeout(DEADLINE):
        while True:
            try:
                response = await client.get("http://127.0.0.1:16686/")
                if response.status_code == 200:
                    break
            except httpx.TransportError:
                pass
            await asyncio.sleep(POLL)
        await compose("exec", "-T", "hirz", "python", "-", stdin=probe.encode())
        # Jaeger's UI JSON endpoint; tied to the pinned Jaeger image.
        # https://github.com/jaegertracing/jaeger/blob/v2.21.0/cmd/jaeger/internal/extension/jaegerquery/internal/http_handler.go
        while True:
            response = await client.get(f"http://127.0.0.1:16686/api/traces/{trace_id}")
            if response.status_code == 200:
                data = response.json()
                if any(row.get("traceID") == trace_id for row in data.get("data", [])):
                    print("PASS Jaeger: disposable trace ingested and retrieved.")
                    return
            await asyncio.sleep(POLL)


async def main(observability: bool = False) -> None:
    token = read_env().get("HA_TOKEN")
    if not token:
        raise DevError("HA_TOKEN is missing; run scripts/init_dev.py first.")
    await check_postgres()
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, trust_env=False) as client:
        async with asyncio.timeout(DEADLINE):
            while True:
                try:
                    response = await client.get("http://127.0.0.1:8000/health")
                    if response.status_code == 200 and response.json() == {
                        "status": "ok"
                    }:
                        break
                    raise DevError("Hirz /health returned an unexpected response.")
                except httpx.TransportError:
                    await asyncio.sleep(POLL)
        print('PASS Hirz: GET /health -> 200 {"status":"ok"} (liveness only).')
        entities = await demo_entities(client, token)
        print(f"PASS HA: {len(entities)} entities; real API, demo devices (simulated).")
        for entity in sorted(DEMO_ENTITIES):
            print("  " + entity)
        response = await client.get(HA_URL + "/api/states")
        if response.status_code != 401:
            raise DevError("Unauthenticated HA state reads did not return 401.")
        print("PASS HA: unauthenticated state read -> 401.")
        if observability:
            await check_jaeger(client)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observability", action="store_true")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.observability))
    except DevError as exc:
        sys.exit(f"FAIL: {exc}")
    except (TimeoutError, httpx.HTTPError):
        sys.exit(
            "FAIL: service check timed out or failed; check Compose service status."
        )
    except Exception:
        sys.exit(
            "FAIL: malformed service response or check failure; no credentials printed."
        )
