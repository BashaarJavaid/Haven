# Verification log

The full evidence behind every `ROADMAP.md` item marked complete (or partially verified): the commands run, the numbers seen, the environment, and the CI run links. `ROADMAP.md` keeps one line per item and links here; `CHANGELOG.md` records what changed. Entries are appended verbatim from the verification that was run, never edited afterwards except to add a later run. See `CLAUDE.md` § Where records go.

---

## Item 1 — Complete (2026-09-17)

Verified: Python **1 passed**; TypeScript **1 passed per workspace**; all lint/type checks and dependency peer checks passed; locked installs left both lockfiles unchanged; `uv build` produced an sdist and wheel, and the wheel imported from a fresh environment outside the checkout. Temporary probes confirmed failing tests return failure in Python and both workspaces, and uncovered Python code fails the 80% gate. Initial Python coverage is 100% over **zero executable statements**, not an application guarantee. Items 2–5 were pending at item 1's completion.

## Item 2 — Complete (2026-09-17)

Verified on Docker Desktop **4.87.0**, Engine **29.7.2**, Compose **5.4.0**, macOS ARM64: authenticated curl returned **123 entities**, including `climate.ecobee`, `cover.garage_door`, `light.bed_light`, and `sensor.outside_temperature`; unauthenticated reads returned **401**; Hirz returned **200 {"status":"ok"}**; Postgres accepted the password-authenticated TCP query. A disposable Compose project passed fresh provisioning, unchanged credentials on rerun, bad/missing token rejection, wrong database password rejection, missing persisted-credential refusal, database-row/onboarding/token persistence across down/up, Jaeger absent by default, and optional-profile trace ingestion/retrieval. Temporary test volumes were removed; development volumes retained. Image manifests include ARM64 and AMD64; only ARM64 was executed. The Hirz image runs non-root without local credentials or dev dependencies. Python **19 passed**, **100% coverage over five runtime statements**; Ruff, strict mypy (including scripts), locked sync, and sdist/wheel build passed. No physical-device or household-action behavior is claimed; items 3–5 remain pending.

## Item 3 — Complete (2026-09-17)

Verified against a clean source snapshot of the implemented checkout, with a separate Compose project, newly generated credentials, and fresh volumes: doctor first reported three PASS and migrations FAIL, then **four PASS / exit 0** after `uv run alembic upgrade head`. Python **36 passed, 86.13% runtime coverage**; PostgreSQL integration **4 passed** in disposable databases (upgrade/repeated upgrade/downgrade/re-upgrade, no seeds, household-scoped account uniqueness and foreign keys, audit shape/default constraints, partial-schema/unknown-revision refusal, and refusal to generate a missing key over audit rows). Reinitialization preserved `.env` byte-for-byte; `alembic check` reported no new upgrade operations. Live invalid database password, invalid HA token, and missing/malformed key probes each returned four results and exit 1 without echoing credentials. Rebuilt non-root container returned `200 {"status":"ok"}`; authenticated HA returned 123 simulated-device entities and unauthenticated reads returned 401. Ruff, strict mypy including migrations, locked sync, sdist/wheel build, and a fresh-wheel CLI check passed. This is schema and diagnostics only: no history, seeds, repositories, pipeline, audit writer, or earned threat-model protection; items 4–5 remain pending.

## Item 4 — Complete (2026-09-17)

Verified: [main push run 35310102678](https://github.com/BashaarJavaid/Hirz/actions/runs/35310102678) passed all **11 jobs** on Ubuntu 24.04 x64 at merge commit `fdc06fca4499794b55a84ffcae6e8203654b2a9b` after PR #1. Python **36 passed, 86.13% coverage**; PostgreSQL integration **4 passed**; TypeScript **1 passed per workspace**. Lint/types, schema drift, four doctor checks, authenticated HA with 123 simulated entities and unauthenticated 401, Hirz liveness 200, package/fresh-wheel checks, non-root UID 10001, and disposable Compose cleanup passed. Five jobs explicitly defer scenario, add-on conformance, latency, Cedar, and release checks; browser tests and frontend bundles also remain deferred. This earns scaffold CI only, not an application or threat-model guarantee. Item 5 retains its separate second-person check.

Manual dispatch on the same main commit also passed all **11 jobs**: [run 35310359507](https://github.com/BashaarJavaid/Hirz/actions/runs/35310359507).

Local verification (2026-09-17): Python **36 passed, 86.13% coverage**; PostgreSQL integration **4 passed** in an isolated source copy with fresh Compose volumes; TypeScript **1 passed per workspace**. Ruff, strict mypy, ESLint, TypeScript, locked installs with unchanged lockfiles, package build/fresh-wheel import and CLI help, workflow YAML and shell syntax, schema-drift check, four doctor PASS results, authenticated HA with 123 simulated entities and unauthenticated 401, Hirz liveness 200, and container UID 10001 passed. Disposable resources were removed and development `.env` remained unchanged.

## Item 5 — Complete (2026-09-18)

Partially verified (2026-09-18): every command in the README's "Scaffold setup" and "Local development stack" sections was executed, on the existing development machine (not a clean one, and not by a second person), and matched the numbers already claimed above — Python **36 passed, 86.13% coverage**; TypeScript **1 passed per workspace**; ruff/mypy/eslint/tsc clean; `uv build` produced sdist+wheel; `hirz doctor` **4/4 PASS**; `check_dev.py` returned **123 HA entities** including all four required entities, unauthenticated 401, liveness 200; the documented stdin `curl --header @-` token check worked; the optional Jaeger profile check passed; PostgreSQL integration **4 passed**; shutdown preserved volumes and `.env`, and `git status` was clean afterward. The README's "## Quickstart" section is unaffected by this and remains unrun target state (`hirz scenario run` and the port-3000 app don't exist yet). This is execution evidence on a non-clean machine by the same person who built it, not the second-person/clean-machine check the verify line calls for — item 5 is not yet complete.

Completed 2026-09-18: a second person followed the README on a clean machine, as the `verify:` line requires, and the author reported that it worked. The author reported the outcome in conversation; the second person's machine, OS, and command output were not captured in this repository. If that output is still available, append it under this heading.

## Item 6 — Complete (2026-09-18)

Implemented and verified on the existing macOS ARM64 development machine with
Python **3.12.13**, uv **0.12.15**, and local Compose PostgreSQL **16.15
(Debian 16.15-1.pgdg13+2)**. This is local evidence, not a new GitHub Actions run.
The approved decisions and bootstrap exception are in
[ADR-002](./adr/ADR-002-postgres-over-dynamodb.md#item-6-amendment--2026-09-18-author-approved);
operating commands are in [development procedures](./development.md).

### Final checks

| Command/check | Observed result |
|---|---|
| `uv sync --locked` | Resolved 46 packages; checked 44 installed packages; no dependency changes |
| `uv run pytest -q` | **68 passed, 11 deselected**, **89.25%** runtime coverage (772 statements, 83 missed); 80% gate passed; 2.70 s |
| `uv run pytest -m integration --no-cov -q` | **11 passed, 68 deselected**; 5.77 s; uniquely named disposable PostgreSQL databases created and removed |
| `.venv/bin/ruff check .` | All checks passed |
| `.venv/bin/ruff format --check .` | 51 files already formatted |
| `.venv/bin/mypy hirz/ scripts/ alembic/` | Success; 17 source files |
| `uv build` | Built `hirz-0.0.0.tar.gz` and `hirz-0.0.0-py3-none-any.whl` |
| Isolated `uv run --isolated --no-project --with <absolute-wheel-path> python -c ...` from `/private/tmp` | Installed 29 runtime packages; imported graph context/seed modules; CLI help listed `doctor`, `seed`, `context`; exit 0 |
| `uv run alembic upgrade head` on the development database | Exit 0; applied the explicit item 6 migration |
| `uv run alembic check` | `No new upgrade operations detected.` |
| `uv run hirz doctor` | **4/4 PASS**, exit 0: authenticated Postgres, HA demo/source label, P-256 signing probe, sole head plus graph tables/materialized view |
| `git diff --check` | No whitespace errors |

The wheel contains all five new graph package files. Seed YAML and checkout-only
migration/procedure files are used from the checkout; the package does not embed
the demo seed files. Neither package build nor the isolated help check claims a
standalone deployed application.

### Database and historical-read evidence

The integration suite exercises fresh upgrade/repeated upgrade/destructive
downgrade/re-upgrade and an existing `0001_initial` household/member/account through
upgrade. Existing identifiers and account links survive; unknown rate/location
facts are not invented. Metadata comparison finds no drift, and removing the
materialized view causes the migration-presence check to fail. The foundation's
existing audit/key-safety tests continue to pass.

Graph tests cover both seeds, untouched semantic repetition, refusal of changed
and evolved households, exact validity boundaries and before-creation reads,
observations received after their measurement time, observation age at the
requested instant, same-time/backdated/stale-version refusal, future and
out-of-order observation rejection, and clearing optional values on replacement.
A new entity cannot be inserted before another entity's latest household write.
Two concurrent edits using one expected version yield **one successful edit and
one version conflict**, with one archived version. Cross-household account foreign
keys and private repository lookups refuse the other home's member. Public
snapshots contain no account subjects or channel/safe-word hashes. A current
context read is observed as **one SQL statement**.

A failure in the second seed rolls back the first seed. An injected materialized
view refresh failure rolls back both new seeds; a separate update-refresh failure
preserves the previous graph, history count, and view contents. No seed operation
writes audit rows or activates a policy.

Service-free tests exercise typed models, malformed/duplicate-key YAML,
references and demo-only input restrictions, historical query bounds, all five
scope projections, household-keyed caches, copy isolation, increasing observation
age, explicit stale-read opt-in, no cached historical reads, no fallback for bad
SQL/malformed data/missing households, and CLI arguments/credential-safe errors.
Actual SQL history and transactional semantics are verified by PostgreSQL, not
inferred from mocked connections.

### CLI runs

`uv run hirz seed constitutions/quinn-home.yaml constitutions/quinn-parents.yaml`
returned exit 0 with:

```text
quinn-home: loaded; household 536fa8ee-854e-56ca-8c5d-5ba418e710a0;
            3 members, 9 assets; constitution 7, unvalidated
quinn-parents: loaded; household bf745178-9146-5952-a310-f1d7e563977b;
               2 members, 2 assets; constitution 1, unvalidated
```

An immediate repeat returned `unchanged` for both households, preserving their
initial `valid_from` of **2026-09-18T17:42:21.620752+00:00**.

The local home UUID with `--scope energy` returned the car, home battery, solar,
and dishwasher (**4 assets, 4 twin bindings, 0 observations**), `stale: false`,
and `policy_status: unvalidated`. The parents' UUID with `--scope people` returned
**2 members, 1 trusted contact, 1 simulated verified Hirz-app method**, and no
private hash/account fields. Malik's contact has no parent-household membership.

The home UUID with `--scope people --as-of 2026-09-18T17:42:21.620752Z` returned
exit 0 with the three initial members and the seeded expected-arrival window.
For an actual historical change, the integration CLI demonstration targets only
a disposable database, runs the real argument parser and serializer, and prints:

```text
Historical CLI: at 12:00Z = Mom; current = Mom updated; preference = 72; both exit 0.
```

That demonstration was also run visibly with
`uv run pytest tests/integration/test_graph_database.py -m integration --no-cov -q -s`:
**7 passed**. Only its connection factory is redirected to the disposable database;
the developer's seeded households were not edited for the demonstration.

### Intermediate failures, limits, and friction check

Initial restricted execution of the old service-free suite returned **34 passed,
2 failed** because the existing WebSocket fixture could not bind localhost
(`PermissionError: [Errno 1] ... operation not permitted`). Docker socket and uv
cache access were likewise restricted; authorized escalation resolved all three.
These repeat [friction-log entry 6](./friction-log.md#entries), not a new upstream
defect. An early test-collection run exposed two new files named `test_graph.py`;
the integration file was renamed `test_graph_database.py`. This was an
implementation mistake, not third-party friction.

Intermediate passes were: **32** new service-free graph tests; **4** original
PostgreSQL tests; then **68** service-free tests at **89.80%** and **9** integration
tests; then **68** at **89.35%** and **10** integration tests after the additional
time/rollback guards. The final results above supersede those intermediate runs.
A heading-only instruction-file parity probe also caught the pre-existing
AGENTS-specific introductory sentence; substantive guidance is synchronized, and
that file-identification difference was retained.

No AWS deployment, new CI run, browser/TypeScript change, 20 ms context benchmark,
production throughput measurement, policy evaluation, signed audit behavior, or
device action was performed or claimed. The running Compose liveness container
was the existing image; Python/CLI checks exercised the updated checkout and the
isolated built wheel. Whole-view refresh serialization and unpartitioned
observation history retain their approved limits. All threat-model rows remain
unchanged. The local database remains migrated and seeded, and the development
stack remains running. Friction-log review found no new entry to add.

## Item 7 — Complete (2026-09-18)

Implemented and verified locally on macOS ARM64, Python **3.12.13**, uv
**0.12.15**, Rust **1.98.1**, Hypothesis **6.168.0**, Docker Engine **29.7.2**,
and the existing local PostgreSQL 16 service. This is **local evidence**; no new
GitHub Actions run or AWS comparison is claimed. The approved semantics and
rejected alternatives are recorded in [ADR-003](./adr/ADR-003-constitution-yaml-to-cedar.md#item-7-amendment--2026-09-18-author-approved-semantics)
and [ADR-004](./adr/ADR-004-no-ml-risk-scoring.md#item-7-catalog-amendment--2026-09-18-author-approved).

### Engine setup and gate

Fetched upstream into `/private/tmp/hirz-item7-dogwood`, checked out
`996d756de1013b7ae209a14f566a80375a59f2f0`, installed Rust into task-specific
temporary directories without changing shell setup, and ran
`cargo build --release -p dogwood-cli`. The revision has no upstream Cargo.lock;
the generated lock is retained in `scripts/dogwood.Cargo.lock`. A subsequent
`cargo build --locked --release -p dogwood-cli` passed. Native binary reports
`dogwood 1.0.0`; an ignored local copy is at `.tools/dogwood`.

The **complete** home policy passed native `validate` with
`passed: true`, `passed_without_warnings: true`, `errors: []`, `warnings: []`.
Parents' full constitution also validated. Native `check-parse` reports **52
policies**, **one temporal policy**, and **one temporal operator**; all resource,
principal, household, class, hash, session and TTL correlations fit that operator.
Matching fields use the native default event schema, including `callerResource`.
The compiled manifest checks 25 temporal policies and a maximum 1440-minute window.

| Gate trace | Actual result |
|---|---|
| Permitted approval request + approved response, then matching unlock | Permit |
| Same unlock without an approval | Deny |
| Approval for another class, same hash | Deny |
| Ten-minute approval presented to a thirty-minute permit | Deny |
| Household A approval presented for household B | Deny |

The suite also checks two genuine TTL groups and two combined household policy
sets, expiry (including permit at exactly 1800 seconds and deny at 1801), rejected
approvals, wrong hashes/resources/principals/sessions, requester/approver/channel/
quorum restrictions, current vetoes and hard bounds after earlier approval, actual
action/class disagreement, governance-action exclusion, and malformed/failed/
timed-out subprocesses. Approval requests are authorized before response events
enter the local replay; the supplied facts do not authenticate a human or passkey.
Unknown action names are escaped and cannot inject trace syntax.

### Final runnable checks

For native checks `HIRZ_DOGWOOD` pointed at the built pinned binary. The tool
sandbox required escalation for loopback/socket and Docker access; no application
credentials were printed and no persistent household rows were changed.

| Command/check | Observed result |
|---|---|
| `uv run pytest` | **182 passed, 11 deselected**, **93.44%** coverage (1813 statements, 119 missed), 80% gate passed; **50.54 s** |
| `uv run pytest -m integration --no-cov` | **11 passed, 177 deselected** at that run, **5.69 s**; corrected seeds exercised in uniquely named disposable databases, then removed |
| `uv run pytest tests/cedar_conformance -k property --no-cov --hypothesis-show-statistics` | **3 passed, 33 deselected**, **27.10 s**; each property reports **200 passing, 0 failing, 0 invalid**, stopped at `settings.max_examples=200` |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 66 files already formatted |
| `uv run mypy hirz/ scripts/ alembic/` | Success; 30 source files |
| `uv build` | sdist and `hirz-0.0.0-py3-none-any.whl` built |
| Isolated wheel installation in `/private/tmp/hirz-item7-wheel`, cwd `/private/tmp` | Both packaged YAML resources load: 21 classes and 21 situation groups; installed CLI validates home with the native binary |
| `docker build --tag hirz-item7:check .` | Passed; pinned Rust builder and dependency lock, native binary copied into existing Python image |
| Container with read-only fixture mount | UID **10001**, Cargo absent, both YAML catalogs load; native full-policy validation, matching-approval permit and no-approval deny passed |
| Final rebuilt container smoke | UID 10001, Dogwood present, Cargo absent, both catalogs packaged |
| `git diff --check` | No whitespace errors |

The three deterministic properties cover bounds/missing/null facts and every role,
condition precedence/ordered overrides and Boolean preflight, and approval traces.
There are **600** generated examples per full property run, all using the native
Dogwood evaluator; this is not a mock engine comparison. Direct cases additionally
cover schedule endpoints, exact-zone occupancy, scoped IDs, membership/time
compilation, all catalog roles/situations, both seeds, schema refusals, immutable
facts, exact YAML decimal text, renderer/YAML round trips, CLI exits, and structured
diagnostics. Worked-example assertions versus downstream work are mapped in
[the constitution spec](./constitution.md#61-what-the-worked-examples-verify-in-item-7).

### CLI output and preview

Ran the actual user workflows (JSON stdout; all exit 0):

```text
uv run hirz constitution validate constitutions/quinn-home.yaml
  valid: true; version: 7; engine: dogwood-local; analysis: not analyzed: local mode
uv run hirz constitution compile constitutions/quinn-home.yaml
  valid: true; policy + schema + manifest; 21 catalog actions; one TTL group (30)
uv run hirz constitution preview constitutions/quinn-home.yaml /private/tmp/hirz-item7-v8.yaml
  Unexpected visitor: ask on phone → never
  Expected arrival: still asks on your phone
  Hirz does not identify the visitor
```

The temporary v8 is a standalone serialization of home v7 with version 8 and
`never_for: [unexpected_visitor]` on door unlock; it was not activated or stored.
Preview also returns changed diagnostic situations and relevant unchanged
situations without UI truncation. The existing stored seeds were inspected in an
explicit `SET TRANSACTION READ ONLY` transaction, then rolled back:

| Stored version | Status | Existing stored hash | Validation result |
|---|---|---|---|
| Home v7 | unvalidated | `e422d43213ce9e97e3150867eb5e48807e5e54f0b1d6bb5fe51d96e3d1cc94c6` | `security.access_code_share: security approval channels must exclude alexa, including never rules` |
| Parents v1 | unvalidated | `d2de39f61464a053eee02ef3973e9d0baef941a042730e147d18d743fa82540d` | Same explicit validation error |

No reseeding, reset, migration, or stored hash rewrite was used to make those old
versions validate. Only the repository seed files' security channels changed.

### Failures corrected and practical limits

Early compiler checks rejected integer-form decimal strings such as `decimal("76")`;
Cedar requires digits on both sides of the decimal point. Early trace serialization
also used Cedar extension syntax, yielding `type error: expected decimal, got
string`; native traces require plain decimal literals. Both implementation errors
were corrected and covered by actual native replay. The first container attempt
excluded the new Cargo lock via `.dockerignore`; adding only that lock to the
allowlist fixed the build. Sandbox GitHub lookup/escalation and the missing
upstream lockfile are recorded in [friction entries 8–9](./friction-log.md).
Earlier successful checkpoints were 109 targeted tests, then 177 full-suite tests
at 92.19%, then 181 at 93.33%; the final expanded suite result is above.

The CLI is usable; no cedarpy fallback or upstream Python-binding change was
needed. The local wrapper replays prefixes for its small approval history rather
than implementing temporal semantics itself. This is a same-process-trust-domain
local evaluator, not an external AWS boundary. `cedar-conform` now requires native
engine/compiler tests and fails for missing tooling; that workflow has not been
run remotely during this task. AgentCore event-schema integration/comparison and
automated reasoning remain item 37. Runtime risk, budgets/quiet hours, graph fact
assembly, activation, authenticated approval/redemption, hash recomputation,
signed audit, device actions and relock are **not** claimed here. All corresponding
threat-model protections remain planned.

### Final review rerun — 2026-09-18

Review found and corrected two implementation issues before handoff: the English
label formatter was replacing decimal points in numeric bounds (`0.3` became
`0 3`), and role/class condition references had redundant boundary fields alongside
the canonical requester role/action class. Numeric rendering now preserves the
value; conditions directly use the same canonical fields as authorization, so
shadow copies cannot disagree. Regression assertions cover both. The first
renderer rerun passed **182 tests**, **93.44%** coverage, **51.25 s**.

After the canonical-field correction, the final command was
`uv run pytest --hypothesis-show-statistics`: **183 passed, 11 deselected**,
**93.40%** coverage (1817 statements, 120 missed), **48.99 s**. Each of the three
native properties again reported **200 passing, 0 failing, 0 invalid** cases.
Ruff passed, formatting checked 66 files, strict mypy passed over 30 source files,
and instruction parity/workflow structure checks passed. The final wheel and
container were rebuilt: installed-wheel compilation outside the checkout and
container UID 10001/native validation/approval permit/no-approval deny all passed,
with explicit checks for numeric English, canonical fields, packaged catalogs,
and absence of Cargo. This supersedes the earlier checkpoint totals above; graph
integration and the preserved stored-seed observations are unchanged.

## Item 8 — Complete (2026-09-18)

Implemented the standalone risk scorer and shared floor function, with the
author-approved semantics recorded in [ADR-004](./adr/ADR-004-no-ml-risk-scoring.md#item-8-amendment--2026-09-18-author-approved)
and [architecture §5.3](../ARCHITECTURE.md#53-risk-engine). The existing catalog's
21 profiles retain their prior base bands, impacts and reversibility strings;
freshness policy is added to that catalog. The constitution validator now uses
the shared floor function. This is scoring and validation, not a runtime pipeline.

### Environment and commands

Local Darwin arm64, Python **3.12.13**, uv **0.12.15**, pytest **9.1.1**,
Hypothesis **6.168.0**, existing pinned native `.tools/dogwood` reporting
**1.0.0**. No dependencies or lockfiles changed. Tooling used
`UV_CACHE_DIR=/private/tmp/hirz-uv-cache` after the sandbox refused the normal
uv cache. The full suite used `HIRZ_DOGWOOD="$PWD/.tools/dogwood"`.

| Command | Observed result |
|---|---|
| `uv run --locked pytest tests/unit/test_risk.py --no-cov -q` | **260 passed in 0.77s**, no warnings |
| `uv run --locked pytest --hypothesis-show-statistics` with sandbox escalation for existing disposable localhost tests | **443 passed, 11 deselected in 49.32s**; **93.75%** runtime coverage (1920 statements, 120 missed), 80% gate passed |
| Native generated conformance, included in that full run | Three properties, each **200 passing, 0 failing, 0 invalid** cases: **600** total |
| Coverage of `hirz/risk/__init__.py` and `hirz/risk/engine.py` | **100% line coverage** each (26 and 77 statements respectively); not a claim of exhaustive runtime security |
| `uv run --locked ruff check .` | `All checks passed!` |
| `uv run --locked ruff format --check .` | `68 files already formatted` |
| `uv run --locked mypy hirz/ scripts/ alembic/` | `Success: no issues found in 31 source files` |
| `uv build` | Successfully built `dist/hirz-0.0.0.tar.gz` and `dist/hirz-0.0.0-py3-none-any.whl` |
| Documented standalone API example | Extracted and executed the exact Python block in [development](./development.md#standalone-risk-scoring-item-8); all assertions passed; output below |
| `git diff --check` | Exit 0, no whitespace errors |

The risk checks cover all classes, matching/nonmatching factors, all 32
combinations of the five applicable HVAC increments, saturation with retained
evidence, stale-factor deduplication, exact freshness/deviation/guard boundaries,
sleep scope, missing and malformed facts, malformed catalog data, injected
exceptions, sanitized failure output, immutable/revalidated facts, deterministic
outputs and unchanged inputs. Both seed constitutions reject static HIGH/CRITICAL
auto changes; dynamically CRITICAL risk keeps `never_auto` across validated
auto/ask/never rule variants. Existing hard bounds still resolve to denial.

### API smoke output

```text
ordinary {"band":"low","base_band":"low","factors":[]} floor=none
escalated {"band":"critical","base_band":"low","factors":[{"factor":"occupant_asleep","effect":"+1 band","evidence":"An occupant is asleep in the affected area."},{"factor":"state_stale","effect":"+1 band","evidence":"Observation age 301.0s exceeds 300s."},{"factor":"deviation_from_baseline","effect":"+1 band","evidence":"Requested temperature differs from requester's preference by 7°F (>6°F)."}]} floor=never_auto
exception {"band":"critical","base_band":"low","factors":[{"factor":"scoring_error","effect":"→ CRITICAL","evidence":"Risk calculation failed."}]} floor=never_auto
```

These are labeled synthetic preview inputs and a deliberately injected exception,
not observed household conditions. No device, model, network service, database,
or active constitution was involved in the smoke example.

### Earlier failures and limits

The first focused run reported **4 failed, 256 passed**. Two test setups compared
a supplied risk rule with different seed-rule bounds; two mode variants retained
per-role restrictions that made the variants invalid constitutions. Corrected the
tests to select matching guards and construct valid variants. A deliberately
bypassed Pydantic fact instance emitted a serialization warning; scoring now
suppresses serialization warnings during its revalidation so malformed values
are not echoed. The focused rerun above passed without warnings.

The first full run inside the sandbox reported **2 failed, 441 passed,
11 deselected in 49.53s**, with the same **93.75%** coverage and all 600 generated
conformance cases passing. Both failures were existing WebSocket token tests
unable to bind a temporary localhost port, not scorer failures. The full rerun
with sandbox escalation passed as recorded above. Cache and socket friction are
recorded once in [friction log entry 6's item 8 follow-up](./friction-log.md).

No remote CI run, AWS comparison, database integration run, frontend checks,
container rebuild or installed-wheel smoke was performed for this Python-only
item. No graph extraction, identity resolution, runtime Decision, approvals,
audit writes, activation, or device execution is claimed. Pipeline integration
is item 9, `hirz decide` item 11, and Protect extraction item 32. Stored seeds
remain unvalidated and unchanged. Runtime threat-model rows remain Planned.

Final documentation review: `git diff --check` passed. A Python comparison of
the catalog against `git show HEAD:hirz/risk/classes.yaml` confirmed all 21 old
profiles are identical after excluding the added freshness field. Comparing
`AGENTS.md` and `CLAUDE.md` from `## Project` onward confirmed matching bodies.
