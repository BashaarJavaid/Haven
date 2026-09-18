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
