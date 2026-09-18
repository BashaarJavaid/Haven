# Development procedures

The existing stack setup and credential recovery procedures remain in the
[README](../README.md#local-development-stack-phase-0-items-2–3) until their planned
move before submission. This page owns the new graph operating procedures.

## Item 6: migrate, seed, inspect

Run from the checkout root with the existing PostgreSQL service and `.env`:

```bash
uv sync --locked
uv run alembic upgrade head
uv run alembic check
uv run hirz doctor
uv run hirz seed constitutions/quinn-home.yaml constitutions/quinn-parents.yaml
uv run hirz context 536fa8ee-854e-56ca-8c5d-5ba418e710a0 --scope energy
uv run hirz context bf745178-9146-5952-a310-f1d7e563977b --scope people
```

The loader prints household UUIDs, member/asset counts, versions, and `loaded` or
`unchanged`. Both policies are **unvalidated**. It never activates a constitution,
creates a signed audit event, calls an adapter, or installs a runtime write API.
The author-approved bootstrap exception is recorded in ADR-002.

Each file has exactly two YAML documents: graph first, constitution second. Only
the two named demo households, `demo` account links and twin bindings are accepted.
Graph keys and references are validated before insertion; duplicate keys are
rejected. Initial versions use the injected transaction clock (UTC wall time in
the CLI); the seeds contain no observation timestamps or invented history.

All files supplied to one command load atomically. Repeat commands compare parsed
contents and stored facts, so comments and formatting do not matter. An untouched
matching household is a no-op. A changed seed, graph edit/history, audit event, or
constitution activation makes the command fail rather than reset data. There is
no `--force` or implicit initialization at startup. Use disposable test databases
for mutation tests, not the existing demo households.

`context` accepts scopes `all` (default), `people`, `member`, `energy`, and
`environment`. `member` requires `--member <uuid>`; other scopes reject it. UUIDs
for members are present in a `people` read. For a historical read:

```bash
uv run hirz context <household-uuid> --scope all --as-of <timezone-aware-ISO-8601>
```

Use an actual graph `valid_from` timestamp or a later recorded instant. Reads
before a household existed and future historical reads fail. Times without a
UTC offset fail argument parsing. History answers what was recorded then; an
observation received later cannot appear in an earlier snapshot even when its
measurement timestamp was earlier.

Output is redacted JSON: no account subjects, channel values/hashes, or safe-word
hashes. Missing measurements stay missing. Source labels distinguish real,
real-API demo devices, and twin data. The read-only command opts into stale
fallback, but caches are per service instance; separate CLI invocations share no
cache, so a fresh CLI invocation cannot read through a database outage. Library
callers default to `allow_stale=False` and must not opt in for decisions.

Success exits 0; operational errors exit 1; invalid command arguments exit 2.
Errors withhold upstream SQL parameters and private values. No command prints
credentials. Doctor checks all graph tables and the materialized view in addition
to its existing service/signing checks. `alembic check` covers table metadata;
PostgreSQL integration tests exercise the view's contents and refresh behavior.

## Verification and recovery

```bash
uv run pytest
uv run pytest -m integration --no-cov
uv run ruff check .
uv run ruff format --check .
uv run mypy hirz/ scripts/ alembic/
uv build
```

Integration tests create uniquely named `hirz_test_*` databases and remove only
those databases. They exercise fresh/populated migrations, historical boundaries,
seed repetition, privacy, version conflicts, concurrent updates, and rollback.
No test executes a household action. The default suite remains service-free with
its 80% coverage gate; its existing WebSocket fixture needs localhost binding.

Migrations remain explicit. If a migration or refresh fails, retain data and fix
the cause; never reset an evolved household to make seeding pass. Item 6 downgrade
destroys its graph additions and history while retaining the foundation tables;
`downgrade base` destroys the application tables as well. Exercise downgrade only
in disposable databases.

Whole-view refresh and graph writers serialize globally. This is the approved
small-graph implementation; neither the 20 ms context budget nor production write
throughput is claimed by item 6. Observation partitioning, real adapter ingestion,
policy activation, auth, and signed audit behavior remain later items.
