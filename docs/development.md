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

## Local constitution workflows (item 7)

Install Rust 1.98.1 with Cargo and a native linker (Apple command-line tools on
macOS; the normal build toolchain on Linux). The build uses the pinned upstream
revision and checked-in dependency lock, needs network access, and writes only a
local binary. No Python bindings or daemon are required.

```sh
uv sync --locked
uv run python scripts/build_dogwood.py
export HIRZ_DOGWOOD="$PWD/.tools/dogwood"
uv run hirz constitution validate constitutions/quinn-home.yaml
uv run hirz constitution compile constitutions/quinn-home.yaml --gateway-resource hirz-local
uv run hirz constitution preview constitutions/quinn-home.yaml /path/to/proposed-v8.yaml
uv run pytest
```

Alternatively put the pinned `dogwood` binary on `PATH`. A missing binary fails
validation/tests; it does not select another engine. The default Gateway resource
is `hirz-local`. Validate/compile output JSON with English, local engine findings,
and `not analyzed: local mode`; compile also includes policy text, action schema,
and a manifest. Preview accepts two complete documents (standalone or seed
envelopes), not an English patch. Diagnostics go to stderr and failures exit
nonzero. None of these commands requires `.env`, a database, credentials or AWS.
Local engine checks do not establish AWS conformance or authenticate approvals.

The container's Rust build stage checks out the same source revision and uses
`scripts/dogwood.Cargo.lock`. Only its native binary reaches the final Python
image; Cargo stays in the builder, and runtime UID remains 10001. Python wheels
carry the class catalog and situation corpus. CI requires native local checks in
`cedar-conform`; AWS comparison remains item 37.

**Existing seed history is preserved.** The files now explicitly give
`security.access_code_share` the `app_push` channel. Old stored seeds inherit
Alexa, so validating them reports `security.access_code_share: security approval
channels must exclude alexa, including never rules`. Their rows, hashes and
`unvalidated` status are not rewritten. Do not reset a household, rerun seeding to
force a change, or edit the stored YAML/hash: the later activation workflow owns
new stored constitution versions. Corrected files can seed a fresh disposable
household for tests. Bootstrap remains the explicit item 6 exception.

## Standalone risk scoring (item 8)

The [risk contract](../ARCHITECTURE.md#53-risk-engine) accepts a canonical Action,
typed facts, and its selected validated Rule. This example uses explicitly
synthetic constitution-preview data; it does not read live observations, access
the database, approve anything, or act on a device. `hirz decide` remains item 11.

Run from the repository root:

```sh
uv run --locked python - <<'PY'
from pathlib import Path
from unittest.mock import patch

from hirz.constitution.preview import situation
from hirz.constitution.schema import load
from hirz.risk import floor_outcome
from hirz.risk.engine import RiskFacts, score

policy = load(Path("constitutions/quinn-home.yaml"))
action, _ = situation(policy, "energy.hvac_adjust")
rule = policy.rule(action.action_class, action.requested_by.role)
ordinary = RiskFacts(observation_ages_seconds=(0,),
                     sleeping_in_target_zone=False, baseline_target_f=72)
escalated = RiskFacts(observation_ages_seconds=(301,),
                      sleeping_in_target_zone=True, baseline_target_f=65)
for label, facts, expected in (("ordinary", ordinary, "low"),
                                ("escalated", escalated, "critical")):
    result = score(action, facts, rule)
    assert result.band == expected
    print(label, result.model_dump_json(), "floor=" + floor_outcome(result.band))
with patch("hirz.risk.engine.guards", side_effect=RuntimeError("injected failure")):
    result = score(action, ordinary, rule)
    assert result.band == "critical" and result.factors[-1].factor == "scoring_error"
    print("exception", result.model_dump_json(), "floor=" + floor_outcome(result.band))
PY
```

The ordinary result is LOW with no floor. Sleep, stale state, and deviation
together reach CRITICAL; the injected exception also produces CRITICAL. Both
have `never_auto` floors. These are synthetic test inputs, not observed household
conditions. To test the implementation, run
`uv run --locked pytest tests/unit/test_risk.py --no-cov`, then the full Python
checks above with the pinned native Dogwood binary available. A sandbox that
cannot write uv's normal cache can set `UV_CACHE_DIR` to a writable temporary
directory; this changes tooling storage only.

## Internal pipeline API (item 9)

The API is `hirz.pipeline.service.Pipeline`: `evaluate`, `propose`, `vote`, `redeem`.
Construct an explicit `PolicyBundle` with `await PolicyBundle.validate(household_id,
policy, Dogwood())`, then supply a SQLAlchemy async connection, `AuditWriter` wrapping
the existing validated signing key, and an injected clock. Mutation methods own their
transaction; pass a connection without an active transaction. The trusted `Principal`
and typed `SupplementalEvidence` are internal integration inputs, not public request
bodies. Construct the one canonical `Action`, then set its `content_hash` with
`hirz.pipeline.hashing.action_hash`. Budget estimates are nonnegative `Decimal` values.
The full API and trust contract is in [architecture §3.4](../ARCHITECTURE.md#34-internal-pipeline-contract-item-9).

With local PostgreSQL running and the existing `.env` initialized, run:

```sh
export HIRZ_DOGWOOD="$PWD/.tools/dogwood"
uv run --locked python scripts/smoke_pipeline.py
```

This runnable internal API example creates a uniquely named `hirz_smoke_*` database,
migrates and seeds it, validates an explicit policy with native Dogwood, evaluates and
proposes a notification authorization, records a vote, redeems once, and retries the
same approval. It asserts one grant and the exact Decimal reservation, then drops only
its disposable database. It reads the existing signing key without changing credentials.
Stored seed policies remain unvalidated. No notification is sent or device operated.
Actual output and checks are recorded once in the [item 9 evidence](./verification-log.md#item-9--complete-2026-09-18).

For the real database checks, `uv run --locked pytest -m integration --no-cov` uses
uniquely named disposable databases, including upgrade/downgrade and metadata agreement.
The internal service does not expose `hirz decide` (item 11), authentication, activation,
physical execution (item 19), or AWS enforcement. Audit append is available internally;
audit verification/export procedures follow below.

## Audit verification and export (item 10)

Run database commands from the checkout root with the existing initialized `.env`
and migrated PostgreSQL. These are local operator commands, not public authenticated
API endpoints. Use a household UUID from the seed/context output:

```sh
uv run --locked hirz verify-audit --household "$HOUSEHOLD_ID"
uv run --locked hirz audit export --household "$HOUSEHOLD_ID" --output audit.json
# Choose an interval that exists in this household; endpoints are inclusive.
uv run --locked hirz audit export --household "$HOUSEHOLD_ID" --range 2:3 --output audit-range.json
```

Exports refuse existing paths and are created with mode `0600`. They include
unchanged signed payloads and may contain household information; there is no
redaction mode. Even a range export checks the entire household chain first.
For command/result and file-format semantics, see
[architecture §5.10](../ARCHITECTURE.md#510-audit-ledger).

To obtain the public key and fingerprint directly from your own trusted local
installation, run the following in the checkout. It prints only public material;
it never generates or replaces a signing key:

```sh
uv run --locked python - <<'PY'
from pathlib import Path
from hirz.audit import fingerprint, public_pem
from hirz.local import read_env, signing_key
key = signing_key(read_env(Path('.env'))).public_key()
print(public_pem(key), end='')
print('Fingerprint:', fingerprint(key))
PY
```

Save just the PEM block as `trusted-public.pem` or retain the fingerprint, and
transfer that trust information separately from an untrusted export. Database
commands may use `--public-key trusted-public.pem` without loading the private
key; they still need `.env` for database credentials. Do not accept a key simply
because it was embedded in the file being checked.

Offline verification needs the installed Hirz CLI but neither PostgreSQL nor `.env`:

```sh
hirz verify-audit --household "$HOUSEHOLD_ID" --file audit.json --public-key trusted-public.pem
hirz verify-audit --household "$HOUSEHOLD_ID" --file audit-range.json --trusted-fingerprint "$TRUSTED_FINGERPRINT"
```

Both commands return JSON and nonzero exit status on failure. `empty` is a
successful check of an empty chain, not proof that history never existed.
`--anchors` is not implemented; all results state the local anchoring limitation.
Do not repair rows, reset pointers or replace keys to make verification pass.
Preserve the original evidence and restore the original key when it is missing.

Run the disposable end-to-end example and concurrency check with:

```sh
export HIRZ_DOGWOOD="$PWD/.tools/dogwood"
uv run --locked python scripts/smoke_pipeline.py --audit
uv run --locked pytest tests/integration/test_audit_database.py -m integration --no-cov -s
```

The smoke extends the existing internal pipeline example. It substitutes only the
CLI's connection factory to target its uniquely named disposable database (the
local CLI deliberately has no database-selection flag); parsing, verification,
file writing, and cryptography are real. Offline commands run as separate installed
CLI processes in a temporary directory without `.env`. It verifies full and range
exports, changes one exported payload, asserts rejection, and removes only its
temporary files and database. No device operation or live-household mutation occurs.
