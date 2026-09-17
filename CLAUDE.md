# CLAUDE.md

Project-specific context and instructions for Haven, merged with a set of general behavioral guidelines (sections 1–5 below, adapted from [andrej-karpathy-skills/CLAUDE.md](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md) and from the author's PortunusMCP conventions) aimed at reducing common LLM coding mistakes: unstated assumptions, speculative complexity, unrelated edits, vague success criteria, and unverified claims of completion.

**Tradeoff:** these guidelines bias toward caution over speed. For trivial tasks, use judgment. When in doubt, ask.

---

## Project

Haven — the bounded-autonomy operating system for the home: a permissioned household agent for Alexa+ (MCP add-on), with a household graph, a user-authored constitution enforced twice (in-process and via AgentCore Policy), a deterministic risk engine, a MILP planner, a protect layer, a digital twin, and a companion web app plus an Alexa+ simulator. Full pitch in `README.md`. Built for the Build, Ship, Shape: Amazon Developer Hackathon 2026 (submission deadline **2026-10-23 12:00 PT**), Alexa+ track primary, Ring track secondary, AWS Builder mini-challenge, and designed as a startup beyond it.

## Where things live

- `README.md` — what this is, the demo story, tech stack, repo layout, quickstart. Read this first.
- `ARCHITECTURE.md` — layers, the Haven loop and the decision pipeline (§3), canonical objects (§4), every component (§5), data model, identity, latency budget, failure modes, hardening, observability, testing, CI, deployment. Load the section relevant to the component being touched, not the whole file.
- `THREAT_MODEL.md` — what's protected, what isn't, assumptions. Load for anything touching the pipeline, constitution, risk, protect, auth, audit, or adapters that act on the world.
- `docs/constitution.md` — the constitution spec, grammar, Cedar compilation. Load for constitution or policy work.
- `docs/tool-catalog.md` — the MCP tool surface and its contract. Load for MCP server or tool work.
- `docs/twin-and-scenarios.md` — twin models and the scenario DSL. Load for adapter, twin, or scenario work.
- `docs/demo-script.md`, `docs/submission.md` — the video and the hackathon checklist. Load for Phase 8 work.
- `docs/friction-log.md` — every friction point hit with a third-party tool, in Devpost's format, plus feature requests. Append to it as friction happens (see Conventions).
- `docs/adr/` — one file per decision with rejected alternatives. Load the specific ADR for the component being touched.
- `ROADMAP.md` — phased build order as a living checklist with `verify:` checks. Check at the start of a session to see what's next; update it as items complete.

## Keeping the instruction files in sync

This project ships the same guidance as `CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex and other agents). They are **not** auto-generated. They are near-identical (only the top heading differs). Whenever you change one — Commands, Current phase, Conventions, or any substantive guidance — mirror the change into the other in the **same commit**.

## Conventions

- **Python 3.12, `uv`, FastAPI, official `mcp` SDK, async throughout** for `haven/`. **TypeScript strict, React, pnpm workspaces** for `apps/`. **CDK in TypeScript** for `infra/`. Ruff and mypy strict for Python; eslint and `tsc --noEmit` for TypeScript. Don't introduce another language or a second web framework.
- **No LLM in any decision.** The pipeline, risk engine, constitution evaluator, planner, executor, and protect weighting are code. Models narrate (Explainer), draft (constitution English → YAML patch), and extract structured signals (Protect) behind schema validation. If a change routes a decision through a model, it is wrong. See `ARCHITECTURE.md` §5.3, §5.4, §5.7, §5.8.
- **No ML risk scoring.** The risk table and factors are the deliberate design (ADR-004), not a gap to fill.
- **The constitution grammar is non-Turing-complete.** No loops, functions, recursion, arithmetic beyond literal comparison. Don't "helpfully" extend it.
- **One canonical shape per object.** `Action`, `Decision`, `Plan`, `AuditEvent`, `VerificationCase` are defined once in `ARCHITECTURE.md` §4 and `haven/pipeline/models.py`. Don't invent a new response shape for a new endpoint or tool.
- **Every state change goes through the pipeline** and produces an audit row. There is no admin path, script, or test helper that executes an action without a `Decision`.
- **Fail closed** for anything whose failure would weaken a guarantee (Postgres, audit write, boundary evaluation, risk exception). If unsure whether something fails open or closed, it's closed. `ARCHITECTURE.md` §9.
- **Twin is labeled.** Every observation carries `source: real | twin`; UI and tool outputs show it. Never present twin data as real.
- **Roles bind to linked accounts, never to voices.** Alexa gives add-ons no speaker identity, so an Echo is a shared device. `security.*` classes are never approvable by voice (approval is in the companion app under a passkey; the validator rejects `alexa` in their `ask_channels`), claimed identity and any speaker hint only lower authority, and Haven never does its own speaker or face recognition. See `ARCHITECTURE.md` §7 and `docs/constitution.md` §2.5.
- **Every tool output has `speakable`** with ≤ 5 options and no internal IDs or JSON in consumer strings; every tool stays under the latency budget (`ARCHITECTURE.md` §8) by never calling a model, a solver, or a third-party network inside the call.
- **Real API contracts, verbatim.** Alexa+ (MCP 2025-11-25, Streamable HTTP, OAuth 2.1 PKCE S256, PRM), AgentCore (Runtime `/mcp` on 8000, CUSTOM_JWT, Gateway policy session header, Cedar/Dogwood quotas), Ring (HMAC-SHA256 webhooks), ComEd, Open-Meteo. When a doc is unclear, fetch it and cite it in the ADR or the code comment; don't guess an API shape.
- **Secrets** only in `.env` (local) or AgentCore Identity (AWS). Never in the graph, the constitution, audit payloads, tests, or docs.
- **AWS spend is bounded.** Pay-per-use services plus exactly two always-on ones, RDS and the worker service (ADR-008, approved 2026-09-16), all deployed for the judging window and destroyed after. Don't add another always-on AWS resource without asking.
- **`THREAT_MODEL.md` rows move only when earned.** A row becomes "Yes" when the item that earns it is built and its `verify:` check passes. Claims never outrun code.
- Relative dates in docs are absolute (`2026-10-23`), never "next week".
- **Friction log, from day one.** Devpost gives up to a 10 percent bonus for it, so it is the cheapest score in the project. Anyone, human or agent, appends an entry to `docs/friction-log.md` at the moment a third-party tool, API, SDK, doc, or CLI did not do what its docs said, cost more than about 15 minutes, or forced a workaround. Log it then, not at the end of the session, because sessions end without warning. At the end of any task that touched a third-party tool, check whether an entry was earned and add it if missed. Entries are facts from the session with the doc URL and the exact error text; never invented, never padded. Severity: `Blocker`, `Major`, `Minor`.

## Commands

Target state; each phase adds its commands here as they become real.

- `uv sync` — install Python deps; `pnpm install` — install workspaces.
- `docker compose -f compose.dev.yml up -d` — Postgres 16 + Home Assistant (demo integration) + Haven.
- `uv run alembic upgrade head` — migrations.
- `uv run haven doctor` — local diagnostics (Postgres, HA, signing key, migrations, constitution compiles); `--aws` adds PRM, `401`, Runtime tool call, Gateway policy decision, scheduler tick.
- `uv run haven decide --action energy.hvac_adjust --params '{"zone":"living_room","target_f":72}' --as malik` — dry-run the pipeline.
- `uv run haven scenario run scenarios/demo-evening.yaml --speed 60` — interactive; `--headless --assert` — CI; `--step --to "18:16"` — pause for recording.
- `uv run haven verify-audit` / `uv run haven audit export --range ...` — audit chain.
- `uv run haven constitution validate|compile|analyze|activate constitutions/quinn-home.yaml` (`analyze` runs AgentCore Policy's automated reasoning and needs AWS credentials; locally it reports "not analyzed").
- `uv run pytest` — tests; `uv run pytest tests/latency` — budget; `uv run pytest tests/cedar_conformance` — both engines.
- `uv run ruff check . && uv run ruff format --check . && uv run mypy haven/`.
- `pnpm -r lint && pnpm -r typecheck && pnpm -r test`; `pnpm --filter web dev` (companion pages + simulator route), `pnpm --filter mcp-app build`.
- `cd infra/cdk && pnpm cdk deploy` / `pnpm cdk destroy` — the AWS stack for the judging window.
- `HAVEN_LLM=off|bedrock`, `HAVEN_ADAPTERS=devices:ha,ev:twin,energy:real,...` — runtime configuration.

## Current phase

**Phase 0 is next: nothing is built yet.** The architecture, threat model, constitution spec, tool catalog, twin spec, demo script, submission checklist, and ADRs are written (2026-09-15). Start with `ROADMAP.md` items 1–5. Do not pull forward Phase 1 work while scaffolding.

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
