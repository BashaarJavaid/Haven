# CLAUDE.md

Project-specific context and instructions for Hirz, merged with a set of general behavioral guidelines (sections 1–5 below, adapted from [andrej-karpathy-skills/CLAUDE.md](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md) and from the author's PortunusMCP conventions) aimed at reducing common LLM coding mistakes: unstated assumptions, speculative complexity, unrelated edits, vague success criteria, and unverified claims of completion.

**Tradeoff:** these guidelines bias toward caution over speed. For trivial tasks, use judgment. When in doubt, ask.

---

## Project

Hirz — house rules for the AI in your home, and your parents': a permissioned household agent for Alexa+ (MCP add-on) that lets a family decide what Alexa may do on its own, what it must ask about, and what it may never do ("bounded autonomy" in the architecture docs). The customer is the family's household manager, responsible for their own home and their parents'; Hirz is rules, not care. It has a household graph, a household-authored constitution (proposed by voice, activated on a phone) enforced in-process, via AgentCore Policy, and by a home agent that obeys only signed commands (Hirz Link), a deterministic risk engine, a MILP planner over real ComEd rate plans, a protect layer, a digital twin, and a companion web app plus an Alexa+ simulator. Full pitch in `README.md`. Built for the Build, Ship, Shape: Amazon Developer Hackathon 2026 (submission deadline **2026-10-23 12:00 PT**): Alexa+ track, Ring track if the item 34 gate passes, both mini-challenges (AWS Builder; Open Source through a separate repository holding an add-on conformance checker and the simulator's host harness), and designed as a startup beyond it. The project was renamed from its first name on 2026-09-17 (`CHANGELOG.md`).

## Where things live

- `README.md` — what this is, the demo story, tech stack, repo layout, quickstart. Read this first.
- `ARCHITECTURE.md` — layers, the Hirz loop and the decision pipeline (§3), canonical objects (§4), every component (§5), data model, identity, latency budget, failure modes, hardening, observability, testing, CI, deployment. Load the section relevant to the component being touched, not the whole file.
- `THREAT_MODEL.md` — what's protected, what isn't, assumptions. Load for anything touching the pipeline, constitution, risk, protect, auth, audit, or adapters that act on the world.
- `docs/constitution.md` — the constitution spec, grammar, Cedar compilation. Load for constitution or policy work.
- `docs/tool-catalog.md` — the MCP tool surface and its contract. Load for MCP server or tool work.
- `docs/twin-and-scenarios.md` — twin models, rate-plan profiles, and the scenario DSL (two demo scenarios). Load for adapter, twin, or scenario work.
- `docs/design.md` — Amazon's design tokens and display modes, per-card specs, the seven hand-designed screens, spoken-line limits. Load for any card, companion-app, simulator, or `speakable` work.
- `docs/demo-script.md`, `docs/submission.md` — the video and the hackathon checklist. Load for Phase 8 work.
- `docs/friction-log.md` — every friction point hit with a third-party tool, in Devpost's format, plus feature requests. Append to it as friction happens (see Conventions).
- `docs/adr/` — one file per decision with rejected alternatives. Load the specific ADR for the component being touched.
- `ROADMAP.md` — phased build order as a living checklist with `verify:` checks. Check at the start of a session to see what's next; update it as items complete.

## Keeping the instruction files in sync

This project ships the same guidance as `CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex and other agents). They are **not** auto-generated. They are near-identical (only the top heading differs). Whenever you change one — Commands, Current phase, Conventions, or any substantive guidance — mirror the change into the other in the **same commit**.

## Conventions

- **Python 3.12, `uv`, FastAPI, official `mcp` SDK, async throughout** for `hirz/`. **TypeScript strict, React, pnpm workspaces** for `apps/`: Tailwind + shadcn/ui for `apps/web`; plain CSS custom properties carrying Amazon's design tokens, and no component library, for the MCP App cards. **CDK in TypeScript** for `infra/`. Ruff and mypy strict for Python; eslint and `tsc --noEmit` for TypeScript. Don't introduce another language or a second web framework.
- **No LLM in any decision.** The pipeline, risk engine, constitution evaluator, planner, executor, and protect weighting are code. Models narrate (Explainer), draft (constitution English → YAML patch), and extract structured signals (Protect) behind schema validation. A model's Protect signals are unioned with the keyword extractor's, so it can add a warning and never remove one, and they feed advice only. The rule preview's situation lines are computed by evaluating both constitution versions, never written by a model. If a change routes a decision through a model, it is wrong. See `ARCHITECTURE.md` §5.3, §5.4, §5.7, §5.8.
- **No ML risk scoring.** The risk table and factors are the deliberate design (ADR-004), not a gap to fill.
- **The constitution grammar is non-Turing-complete.** No loops, functions, recursion, arithmetic beyond literal comparison. Don't "helpfully" extend it.
- **One canonical shape per object.** `Action`, `Decision`, `Plan`, `AuditEvent`, `VerificationCase` are defined once in `ARCHITECTURE.md` §4 and `hirz/pipeline/models.py`. Don't invent a new response shape for a new endpoint or tool.
- **Every state change goes through the pipeline** and produces an audit row. There is no admin path, script, or test helper that executes an action without a `Decision`.
- **Fail closed** for anything whose failure would weaken a guarantee (Postgres, audit write, boundary evaluation, risk exception). If unsure whether something fails open or closed, it's closed. `ARCHITECTURE.md` §9.
- **Twin is labeled.** Every observation carries `source: real | real API, demo devices | twin`; tool outputs and detail views show it. Cards show two states, `live` and `simulated` (anything not plainly `real` shows as simulated). A published rate table is `real (published ComEd rate)`, never "live". Never present twin data as real. Hosted-demo households bind `twin` adapters only. Falling back from a real device to its twin is a scenario and demo feature: in a real household an unreachable device is `unavailable; actual state unknown`, and a twin read-back never verifies a real device.
- **No Hirz process outside the home holds a device credential in AWS mode.** The Home Assistant token stays with Hirz Link in the house; the home obeys only commands signed by the KMS key that only the `hirz-actions` Lambda role may use; write-capable cloud credentials are readable by that role only. A change that hands the worker or the `mcp` role something it can act with is wrong (ADR-009). Local mode has no outside boundary and is labeled `dogwood-local`. The claim covers bugs and bypass paths, not a compromised worker (`THREAT_MODEL.md`; ADR-010 and item 38d narrow that for `security.*`). The signer recomputes the action hash and never trusts the worker's; a command names one home and runs once; and Link owns the ending of a bounded operation, so a relock never depends on the cloud. Hirz governs the actions Hirz takes: never write that it controls everything Alexa can do.
- **A voice proposes, a phone activates.** Rule changes spoken to Alexa are proposals (`propose_household_rule`); activation is passkey-gated in the companion app. Same principle as security approvals.
- **A fair comparison, without hindsight.** The headline saving is against the timer schedule a careful household already uses, with "do everything now" and the cheapest-slots heuristic beside it, all held to the same comfort, delivered EV energy, and final battery state. The backtest plans only from what was knowable at the time and bills at realized prices, and it includes a home with no solar or battery.
- **Numbers are derived, never typed.** Every dollar and kWh figure in the product, the README, the video, and the Devpost text comes from a cited scenario run or the backtest in `scripts/`; rate tables carry their source URL and effective date.
- **Roles bind to linked accounts, never to voices.** Alexa gives add-ons no speaker identity, so an Echo is a shared device. `security.*` classes are never approvable by voice (approval is in the companion app under a passkey; the validator rejects `alexa` in their `ask_channels`), claimed identity and any speaker hint only lower authority, and Hirz never does its own speaker or face recognition. Provenance is the linked account and the surface; a name inside a sentence is `claimed_author`, shown as claimed. A schedule is context, never identity: no string says who is at the door ("Someone is at the front door. Mom is expected now."). See `ARCHITECTURE.md` §7 and `docs/constitution.md` §2.5.
- **Every tool input is flat** (enums and scalars in consumer language; no free-form objects, no internal class names). **Every tool output has `speakable`** with a headline of about 20 words or fewer, ≤ 5 options, and no internal IDs or JSON in consumer strings. A `speakable` never states what Hirz was not told (a caller's number), never promises an outcome the boundary has not yet allowed, and never assumes Alexa can speak later: a delayed result (a contact's reply, a re-plan) reaches the card and the phone, and is spoken only when the member asks again. Every tool stays under the latency budget (`ARCHITECTURE.md` §8) by never calling a model, a solver, or a third-party network inside the call.
- **Real API contracts, verbatim.** Alexa+ (MCP 2025-11-25, Streamable HTTP, OAuth 2.1 PKCE S256, PRM; the add-on design guide's tokens and display modes, `docs/design.md`), AgentCore (Runtime `/mcp` on 8000, CUSTOM_JWT, Gateway policy session header, Cedar/Dogwood quotas), Ring (HMAC-SHA256 webhooks), ComEd, Open-Meteo. When a doc is unclear, fetch it and cite it in the ADR or the code comment; don't guess an API shape.
- **Secrets** only in `.env` (local) or AgentCore Identity (AWS); the audit key uses a mounted secret in deployment. Locally, `AUDIT_SIGNING_KEY` is quoted multiline unencrypted PKCS#8 P-256 PEM in regular, nonsymlink `.env` mode `0600`, generated by explicit initialization only after confirming no audit history and a consistent or completely unmigrated schema. Never replace a malformed key or regenerate over audit history; restore the original. Never put secrets in the graph, the constitution, audit payloads, tests, or docs.
- **AWS spend is bounded.** Pay-per-use services plus exactly two always-on ones, RDS and the worker service (ADR-008, approved 2026-09-16), all deployed for the judging window and destroyed after. Approved pay-per-use additions (2026-09-17): one KMS signing key, one S3 Object Lock anchor bucket, the community Skill bridge's stack for the recording only, Bedrock usage by the rate-limited hosted demo, the `hirz-passkeys` Lambda with its Parameter Store entries (item 38d), and the one-minute EventBridge rule that drives the worker's tick. Don't add another always-on AWS resource without asking.
- **`THREAT_MODEL.md` rows move only when earned.** A row becomes "Yes" when the item that earns it is built and its `verify:` check passes. Claims never outrun code.
- Relative dates in docs are absolute (`2026-10-23`), never "next week".
- **Friction log, from day one.** Devpost gives up to a 10 percent bonus for it, so it is the cheapest score in the project. Anyone, human or agent, appends an entry to `docs/friction-log.md` at the moment a third-party tool, API, SDK, doc, or CLI did not do what its docs said, cost more than about 15 minutes, or forced a workaround. Log it then, not at the end of the session, because sessions end without warning. At the end of any task that touched a third-party tool, check whether an entry was earned and add it if missed. Entries are facts from the session with the doc URL and the exact error text; never invented, never padded. Severity: `Blocker`, `Major`, `Minor`.

## Commands

Available after Phase 0 items 1–3: dependency installs, Python and TypeScript
tests, lint/type checks, `uv build`, and the local Compose stack with explicit
initialization and service checks, Alembic migrations, and the local doctor. The other commands below remain target state.
The verified toolchain and scaffold setup are in `README.md`; use Node 24.

- `uv sync` — install Python deps; `pnpm install` — install workspaces.
- `uv sync --locked` / `pnpm install --frozen-lockfile` — reproduce locked dependencies; `uv build` — build the Python sdist and wheel.
- `uv run python scripts/init_dev.py` — initialize local credentials and HA demo onboarding; preserves existing state.
- `docker compose -f compose.dev.yml up -d` — Postgres 16 + Home Assistant (demo integration) + Hirz liveness server.
- `uv run python scripts/check_dev.py` — authenticated database/HA checks and `/health`; `--observability` also checks a disposable trace after starting the optional Jaeger profile.
- `docker compose -f compose.dev.yml --profile observability down` — stop services, preserving named volumes; README documents recovery and the separate destructive reset.
- `uv run alembic upgrade head` — explicit local migrations; never applied at startup. `downgrade base` destroys the five foundation tables and is for disposable data only.
- `uv run hirz doctor` — four read-only local checks: Postgres, HA demo entities, P-256 signing probe, migration head/table presence. Exit 0 only if all pass; no `--aws` or constitution check yet. Those checks remain target state.
- `uv run hirz decide --action energy.hvac_adjust --params '{"zone":"living_room","target_f":72}' --as malik` — dry-run the pipeline.
- `uv run hirz scenario run scenarios/demo-evening.yaml --speed 60` — interactive; `--headless --assert` — CI; `--step --to "18:16"` — pause for recording.
- `uv run hirz verify-audit` (`--anchors` also checks the S3 anchors in AWS mode) / `uv run hirz audit export --range ...` — audit chain.
- `docker compose -f compose.link.yml up -d` — Hirz Link beside Home Assistant, in the home (AWS mode).
- `uv run python scripts/backtest.py` — the year-long rate-plan backtest every published savings figure comes from.
- `uv run hirz constitution validate|compile|analyze|activate constitutions/quinn-home.yaml` (`analyze` runs AgentCore Policy's automated reasoning and needs AWS credentials; locally it reports "not analyzed").
- `uv run pytest` — service-free tests (80% coverage gate); `uv run pytest -m integration --no-cov` — live PostgreSQL tests in uniquely named disposable databases; `uv run pytest tests/latency` — budget; `uv run pytest tests/cedar_conformance` — both engines.
- `uv run ruff check . && uv run ruff format --check . && uv run mypy hirz/ scripts/ alembic/`.
- The add-on conformance checker (separate open-source repository, name to be chosen) run against the local MCP server.
- `pnpm -r lint && pnpm -r typecheck && pnpm -r test`; `pnpm --filter web dev` (companion pages + simulator route), `pnpm --filter mcp-app build`.
- `cd infra/cdk && pnpm cdk deploy` / `pnpm cdk destroy` — the AWS stack for the judging window.
- `HIRZ_LLM=off|bedrock`, `HIRZ_ADAPTERS=devices:ha,ev:twin,energy:real,...` — runtime configuration.

## Current phase

**Phase 0 items 1–3 are complete and verified (2026-09-17); item 4 is implemented, pending green CI on `main`.** The eleven-job GitHub Actions workflow runs existing scaffold checks and explicitly labels future checks as successful placeholders. The author merges the `phase-0` PR for items 1–4; verify the resulting main run before recording item 4 complete in a follow-up documentation PR. Do not treat placeholder success as an application guarantee. The Python package and both TypeScript workspaces have tests, lint/type checks, and locked dependencies. The localhost-only Compose stack has Postgres 16, HA demo devices with automated token provisioning, a Hirz `/health` endpoint, and optional Jaeger. Alembic creates five foundation tables with UUID identities, household-scoped account links, and per-household audit pointers. Explicit initialization provisions a local signing key; `hirz doctor` gives four PASS results after migration on a clean source snapshot with fresh volumes. Python: 36 passed, 86.13% runtime coverage; live PostgreSQL integration: 4 passed. Ruff, strict mypy including migrations, locked sync, build, fresh-wheel CLI, invalid-credential/key checks, and unchanged credentials on reinitialization passed. These are scaffold checks, not application guarantees. No household application behavior, graph history/repositories/seeds, audit writer, MCP, or worker is built. The architecture, threat model, constitution spec, tool catalog, twin spec, demo script, submission checklist, and ADRs are written (2026-09-15) and were revised on 2026-09-17 after a full critique against the hackathon rules (named customer and two homes, three-beat demo, rule authoring by voice, ComEd Time-of-Day rate plan, design spec, Hirz Link and signed commands, deeper Ring use, the separate open-source repository, audit anchors, hosted demo, rename); the `CHANGELOG.md` entry for that date is the summary and `ROADMAP.md` carries the new cut line. A second, external critique was worked through the same day (authorization chain, visitor and scam semantics, async conversation honesty, local relock, fair backtest, derived rule preview, pause, ADR-010); it has its own `CHANGELOG.md` entry. Continue with `ROADMAP.md` items 4–5. Do not pull forward Phase 1 work while scaffolding.

---

## 1. Ask before deciding

**Don't assume. Don't hide confusion. Surface tradeoffs. Ask.**

The author's standing instruction for this project: **when a question comes up, ask rather than decide, assume, or guess.** That includes product choices, naming, scope, API shapes not covered by a doc, which adapter to make real, what to cut, and anything about money (AWS spend) or the hackathon submission.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them; don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

This project's design has been reviewed and most ambiguity is resolved in writing in `ARCHITECTURE.md`, `THREAT_MODEL.md`, `docs/`, and `docs/adr/`. Check there first; if it's genuinely not covered, that's exactly what to surface. Batch questions when you can, so the author answers once.

## 2. Simplicity first

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked and what the current `ROADMAP.md` phase calls for. Don't pull forward a Phase 5 feature while working on Phase 2.
- No abstractions for single-use code. No plugin systems where a function list will do (the adapter registry and the risk table are deliberately plain).
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios; do implement the fail-closed handling `ARCHITECTURE.md` §9 explicitly calls for.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical changes

**Touch only what you must. Clean up only your own mess.**

- Don't "improve" adjacent code, comments, or formatting. Don't refactor what isn't broken. Match existing style.
- If you notice unrelated dead code, mention it; don't delete it.
- Remove imports/variables/functions that *your* change made unused. Leave pre-existing dead code unless asked.

The test: every changed line traces to the current task or `ROADMAP.md` item.

## 4. Goal-driven execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add the TOCTOU guard" → "Write a test that mutates params between approval and redemption and asserts `DENY_APPROVAL_MISMATCH`, then make it pass."
- "Add the EV twin" → "Write a test that 34→50% at 7.4 kW takes 100–110 minutes, then make it pass."
- "Wire the planner" → "The demo scenario's headless assertion passes with savings in range."

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```
`ROADMAP.md` already carries a `verify:` per item and `ARCHITECTURE.md` §12 defines the test strategy; use them as the source of success criteria instead of inventing new ones per task.

## 5. Run it and show it

**Nothing is done until it has been run and the output is shown.**

The author's second standing instruction: **after building a feature, run and verify it, and report what you saw.** Concretely:
- Run the relevant tests and paste the summary line (passed/failed/coverage).
- Run the feature the way a user would: the CLI command, the scenario, the tool through MCP Inspector or the client SDK, the page in the browser via Playwright or a screenshot. Paste the output or describe exactly what rendered.
- If something could not be verified (no AWS credentials, no Bedrock access, a service down), say so first and plainly, and mark the item as not done in `ROADMAP.md`.
- Never write "should work", "is now complete", or tick a roadmap item on the strength of code alone.
- Report failures faithfully with the output. A failing test reported honestly is progress; a green claim that isn't is a regression.
- If the task touched a third-party tool, check `docs/friction-log.md`: was an entry earned? Add it before reporting done.

---

**These guidelines are working if:** clarifying questions come before implementation rather than after mistakes; diffs are small and traceable to a roadmap item; every completed item has a pasted verification; `THREAT_MODEL.md` never claims more than the code does; and the phase boundaries in `ROADMAP.md` hold.
