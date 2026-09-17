# Roadmap

The build order for Haven, sequenced so there is something demoable at the end of every phase. Kept as a living checklist: update this file as items complete rather than letting it drift from reality. Items are complete only when their `verify:` check passes and, where a `THREAT_MODEL.md` row is involved, the row is earned by code.

**Hackathon dates (Build, Ship, Shape: Amazon Developer Hackathon 2026):**

| Milestone | Date |
|---|---|
| AWS promotional credit request deadline | 2026-10-21 12:00 PT |
| **Submission deadline** | **2026-10-23 12:00 PT** |
| Judging period | 2026-11-09 to 2026-11-20 |
| Winners announced | on or about 2026-12-03 |

Haven is designed as a startup; the hackathon is its first milestone. Phases 0–8 are the hackathon build with a **cut line** after Phase 8. Phase 9 onward is the company. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for what each item means and [`docs/adr/`](./docs/adr/) for the reasoning behind deferrals.

---

## Build order

**Phase 0 — Scaffold (repo, stack, and the everyday loop)**
1. Repo scaffold: `uv`-managed Python 3.12 package `haven/`, `pyproject.toml` (ruff, mypy strict, pytest with 80% gate), `apps/` workspaces with pnpm, `LICENSE` (Apache-2.0), `.gitignore`, `CLAUDE.md`/`AGENTS.md` at parity — *verify:* `uv run pytest` and `pnpm -r test` run green on empty suites; `ruff`, `mypy`, `tsc` pass.
2. `compose.dev.yml`: Postgres 16, Home Assistant with the `demo` integration pre-configured and a long-lived token provisioned by a one-shot init script, Haven container, optional `observability` profile (Jaeger) — *verify:* `docker compose -f compose.dev.yml up -d` then `curl localhost:8123/api/states` returns demo entities.
3. Alembic initialized with the `households`, `members`, `member_accounts`, `audit_log`, `audit_pointer` tables and `haven doctor` (checks Postgres, HA, signing key, migrations) — *verify:* `haven doctor` reports all PASS on a fresh clone.
4. GitHub Actions per `ARCHITECTURE.md` §13 with every job present (some trivially green) — *verify:* CI green on `main`.
5. Docs skeleton is the one in this repo; `README.md` quickstart commands work as written — *verify:* a second person follows the README on a clean machine.

**Phase 1 — Core decision engine (bounded autonomy, provable, on the CLI)**
6. Household Graph models, repositories, row versioning, `Context Service` read model with the materialized `household_context` view; seed loader for `constitutions/quinn-home.yaml` — *verify:* unit tests for versioned reads at a past instant; seed loads.
7. Constitution: Pydantic schema, class list (`haven/risk/classes.yaml`), condition grammar and evaluator, tighten-only validation, voice-never-approves-security validation (`docs/constitution.md` §2.5), `requester.surface` attribute, plain-English round-trip renderer, Cedar/Dogwood compiler (generic temporal permit per TTL, `docs/constitution.md` §4), and the Dogwood CLI subprocess wrapper — *verify:* `tests/unit/test_constitution.py` incl. the missing-attribute-inside-`not` case; a `security.*` rule with `alexa` in `ask_channels` fails validation; an `override` that loosens its rule's base mode fails validation; every worked example in `docs/constitution.md` §6 resolves as documented; **Dogwood gate:** the CLI validates the compiled set for `quinn-home` and replays a two-event trace (approve, then act, same `action_hash`) to `permit`, and the same act without the approval to `deny`. If the gate fails, switch to the documented fallback (`cedarpy` plus an in-process record for the one generic temporal rule) and update `docs/constitution.md` §4 before continuing.
8. Risk Engine: static table, dynamic factors, floors in one function — *verify:* factor tests; CRITICAL floor cannot be loosened by any constitution; exception → CRITICAL.
9. Decision Pipeline with the canonical `Decision`, budgets, approvals table with `content_hash` binding and TTL — *verify:* pipeline precedence tests for every terminal; approval TOCTOU test → `DENY_APPROVAL_MISMATCH` (earns the THREAT_MODEL row).
10. Audit Ledger: hash chain, ECDSA signing, `haven verify-audit`, `haven audit export` — *verify:* chain contiguity under 100 concurrent decisions; verifier rejects a mutated row.
11. `haven decide` CLI (dry-run a hypothetical action against the active constitution) — *verify:* the eight worked examples produce the documented event types.

**Phase 2 — Twin, adapters, and scenarios (the world Haven reasons about)**
12. Adapter protocols and registry with `source` stamping; `HAVEN_ADAPTERS` config — *verify:* registry tests; a mixed real/twin configuration boots.
13. Twin models: thermal zones, EV, home battery, PV, appliances, tariff, occupancy, wearable, devices, contacts, doorbell; `SimClock` — *verify:* physics tests (energy conservation, SoC bounds, 34→50% takes ~1 h 45 min at 7.4 kW, pre-warm 4 °F in ~45 min).
14. Real adapters with no credentials: ComEd Hourly Pricing (day-ahead + 5-minute), Open-Meteo — *verify:* live fetch tests with recorded fixtures for CI.
15. Home Assistant adapter (WebSocket subscribe + REST services) against the demo integration, plus one physical device: an energy-monitoring smart plug with a local HA integration (Kasa KP125 or Shelly Plus Plug class) bound to `light.living_room` through `asset_bindings`, everything else twin — *verify:* set a demo climate target and read it back through the adapter; switch the plug on through the pipeline, read the state back from the device, and see its power draw arrive as an observation with `source: real`; the twin binding takes over when the plug is absent.
16. Scenario DSL, runner, headless scripted host, `haven scenario run|step` — *verify:* `scenarios/demo-evening.yaml` runs headless through all events with observations asserted (planner not yet present).

**Phase 3 — Planner, coordinator, executor, scheduler, memory (Haven acts)**
17. Planner: MILP formulation on HiGHS, baseline-plan savings computation, alternatives, `explain.facts`; greedy heuristic; **savings range derived from data**: record at least two weeks of ComEd day-ahead and 5-minute prices, run the planner on the demo loads for each day, and replace the provisional `estimated_savings_usd` range in `scenarios/demo-evening.yaml` with the observed spread (script and data in `scripts/`) — *verify:* tiny-instance optima match hand computation; demo evening solves in < 2 s; `peak_kwh_avoided` and savings in the derived range; the derivation script reproduces the range from the stored data.
18. Coordinator: constraint intake, conflict detection, precedence, quorum — *verify:* the Dad-kitchen constraint moves the dishwasher after 23:00; an unreachable EV deadline produces a conflict, not a silent drop.
19. Executor: lifecycle, idempotency, execution-time re-evaluation, verify-after-act, rollback, deadlines; local scheduler on the sim clock; the `mcp` / `worker` role split with "act" tools writing `scheduled`-for-now actions the worker sweep executes — *verify:* an "act" tool returns `status: executing` without touching an adapter and the worker executes it within one sweep; HA demo read-back mismatch → `VERIFY_FAILED` then retry; someone falling asleep before a scheduled HVAC change turns it into ASK.
20. Memory: Postgres session memory, AgentCore Memory interface with an in-process implementation, consent-gated proposals — *verify:* a proposal is never used by the planner until accepted.
21. Explainer with `HAVEN_LLM=off` templates and the Bedrock implementation behind one interface; invented-number guard — *verify:* output schema tests; a fabricated figure is rejected.
22. Scenario assertion for the demo evening now covers plan, revisions, executions, and the overnight sequence — *verify:* `haven scenario run scenarios/demo-evening.yaml --headless --assert` passes end to end (trust and doorbell events still no-op).

**Phase 4 — MCP server and tool catalog (the Alexa+ contract)**
23. Streamable HTTP server on the official SDK, Host/Origin validation, body bounds, stateless default — *verify:* MCP Inspector connects; `initialize → tools/list → tools/call` via the Python client SDK.
24. OAuth: PRM document, `401` + `WWW-Authenticate`, JWT validation against a local dev issuer with PKCE S256, scopes, member mapping, guest experience — *verify:* the SDK's OAuth client completes discovery and linking against the dev issuer; wrong `aud` → 401.
25. All eleven tools (`docs/tool-catalog.md`) with `inputSchema`/`outputSchema`, `speakable`, consumer-language errors, presentation hints — *verify:* schema conformance test over every tool; UX conformance test (≤5 options, no IDs, speech-length estimate); `approve_action` for a `security.*` class over the `alexa` surface never resolves the approval and its `speakable` points to the phone; a tool-selection test drives every demo utterance through the emulator and asserts the intended tool was chosen.
26. Latency suite and household isolation test — *verify:* p95 per tool ≤ 250 ms over the corpus; two-household leak test passes (earns the THREAT_MODEL row).
27. MCP App cards with `@modelcontextprotocol/ext-apps`: plan, approval, verification, doorbell, scorecard — *verify:* cards render in the ext-apps reference host and call tools through the bridge only.

**Phase 5 — Companion app and Haven Simulator (what the judges see)**
28. Web app (`apps/web`, one React app with routes; the simulator is one of them, item 29): Tonight, Approvals (web push), Constitution (form, YAML, English drafting with diff, Cedar view, analysis findings in AWS mode with a "not analyzed: local mode" notice otherwise, history, rollback), Household, Audit, Twin — *verify:* Playwright: edit a rule in English → diff → activate → `CONSTITUTION_ACTIVATED` row; approve an action from push.
29. Simulator, a route of the single web app: emulated host (Strands on Bedrock, Claude Haiku 4.5 by default with Nova Lite selectable; scripted fallback when `HAVEN_LLM=off`), MCP Apps host bridge, voice in/out, Echo Show and Echo Dot modes, tool-call transcript, honesty banner naming the model in use — *verify:* the demo evening completes in both modes; voice-only mode never depends on a card.
30. Demo seed and `compose.demo.yml` with the scenario paused at 17:30 — *verify:* one command brings up the recording state.

**Phase 6 — Protect and Ring (Haven protects)**
31. Trusted contacts with out-of-band channel verification; companion app check-in flow; safe word (hash only); verified email — *verify:* a presented number that matches nothing is reported as unverified; a check-in reply closes the case.
32. `assess_request_risk` signals (keyword extractor offline, Bedrock structured extraction online) with code-weighted bands; `scam_pattern` factor — *verify:* the demo scam relay lands CRITICAL; a benign "Dad wants to know when dinner is" lands LOW.
33. Organization verification (`assess_request_risk` with `claimed_party: organization`) with saved contacts and the curated registry — *verify:* utility number saved at onboarding matches; a lookalike does not.
34. Ring adapter, gated. **Access gate first, before any other Phase 6 work:** register the app in the Ring Developer Portal, obtain sandbox credentials and the HMAC signing key, and receive a synthetic `button_press` webhook with a valid signature at a local endpoint, without owning a Ring device — *verify:* the signed event is logged with its payload. **Gate passes →** Ring-driven app-integration linking (HMAC nonce; partner-initiated OAuth is invitation-only), HMAC-signed webhooks with replay window, sandbox synthetic doorbell events, snapshot retrieval, doorbell card, expected-visitor context; the unlock with auto-relock is the `devices` adapter's lock through the pipeline (Ring has no lock API) — *verify:* a Ring sandbox press reaches the card; a forged signature is dropped and audited (earns the row); unknown visitor unlock → `DENY_CONSTITUTION`. **Gate fails (no credentials, or a physical device is required) →** drop the Ring track entry, keep the twin doorbell (the demo door beat is unchanged), mark the "Forged Ring doorbell event" threat-model row not applicable, and remove Ring from `docs/submission.md` and the README banner.
35. Demo scenario now asserts the full sequence in `docs/twin-and-scenarios.md` §3 — *verify:* passes headless.

**Phase 7 — AWS (AgentCore runs Haven's enforcement and state)**
36. CDK stack: Cognito (PKCE), AgentCore Runtime (`mcp` role, MCP protocol, CUSTOM_JWT), worker service (`worker` role, App Runner smallest size, HTTPS; Fargate + ALB as fallback), Gateway + policy engine + `haven-actions` Lambda target, Memory, Identity credential providers, EventBridge Scheduler + tick Lambda targeting the worker, RDS (smallest class), Bedrock access, CloudWatch — *verify:* `cdk deploy` idempotent; `cdk destroy` leaves nothing billable; the companion API answers over HTTPS from the worker.
37. Cedar/Dogwood compiler wired to the policy engine; generic temporal approval rule; policy session ids on Gateway calls; automated-reasoning validation (`validationMode`) on policy create/update wired into activation; `LOG_ONLY` first — *verify:* `tests/cedar_conformance`: zero disagreements between the Dogwood CLI and AgentCore over the corpus; activation of a deliberately always-allow constitution is refused with the AgentCore finding; then switch to `ENFORCE` (earns the boundary-agreement row at its "Partial" wording).
38. Runtime deployment of the Haven image in the `mcp` role and worker deployment in the `worker` role; PRM and `401` served by the Runtime; Bedrock explainer and emulator on real models; Memory strategies live — *verify:* `haven doctor --aws` passes every check in `ARCHITECTURE.md` §14, including an "act" tool call whose action the worker executes and verifies within 10 s; `tests/latency` reports warm p95 under budget and the measured Runtime cold-start time, which is logged in `docs/friction-log.md`.
39. Cost guard: tagged resources, a budget alarm at $40, teardown runbook — *verify:* Cost Explorer shows the judging-window run under budget.

**Phase 8 — Submission (the cut line)**
40. Demo video per `docs/demo-script.md`, recorded from the simulator in Echo Show mode with a voice-only cut for one beat, under 3 minutes, no third-party marks or music — *verify:* watched by two people who did not build it; every claim on screen maps to an audit row in the cited scenario run; every dollar and kWh figure in the video, the README, and the Devpost description is the value from that run, never typed.
41. README final pass, product feedback per tool, friction log entries (each with the exact URL and error text), feature requests, judge run instructions (no-credential path), Devpost form: Alexa+ primary, Ring secondary if the item 34 gate passed, both mini-challenges (AWS Builder and Open Source) if the form allows selecting both, and at least one real upstream pull request opened during the window (candidate: the MCP Python SDK's missing User-Agent header, if still open) cited in the Open Source entry and the friction log — *verify:* `docs/submission.md` checklist fully ticked; credits requested before 2026-10-21.
42. Tag `v0.1.0`; release notes in `CHANGELOG.md` — *verify:* a clean-machine quickstart by someone else reaches the plan card.

---

## Cut line and fallbacks

If the schedule slips, the minimum credible demo is Phases 0–5 plus items 31–32 and 36–38. Ring (34) and organization verification (33) are the first to defer; the Ring track entry is dropped if the access gate in 34 fails or if 34 is not real. Dropping Ring does not touch the Alexa+ entry: the door beat runs on the twin doorbell and Alexa+ judges do not score Ring usage. Nothing below Phase 5 may be cut: without the simulator there is no demo.

Suggested calendar from 2026-09-15: Phase 0–1 by 09-24, Phase 2–3 by 10-03, Phase 4 by 10-08, Phase 5 by 10-13, Phase 6 by 10-16, Phase 7 by 10-19, Phase 8 by 10-22. Dates are targets, not gates; the gates are the `verify:` checks.

---

## Phase 9 onward — the company (documented, not built)

Each item has a trigger so it is built when needed, not speculatively.

- **Physical-Echo Skill bridge.** Trigger: access to an Alexa+ device. The community bridge pattern (a classic Skill fronting a Strands agent on AgentCore Runtime that speaks to Haven's MCP server) gives a hardware demo without add-on access. ADR-007.
- **Real add-on certification.** Trigger: Alexa+ add-on developer access. The MCP server, PRM, and MCP Apps are built to the contract; certification adds store metadata, privacy policy, and the functional test pass.
- **Telephony call-backs.** Trigger: first household that wants verified-number callbacks. A `contacts` adapter over a telephony provider; the verification method already exists in the constitution.
- **Native mobile app.** Trigger: push-approval latency or biometrics become a product requirement. The companion API is already the contract.
- **Device breadth.** Trigger: any real home. Home Assistant covers most of it; direct adapters (Matter, Tesla Fleet, Enphase) follow demand.
- **Virtual power plant aggregation.** Trigger: 100 households on real energy adapters. A demand-response goal term and a program-operator adapter over the existing planner model.
- **Constitution templates and sharing.** Trigger: onboarding friction data. Templates for common household shapes with analysis reports.
- **Multi-replica Runtime and per-household locking.** Trigger: measured contention. Today one Runtime session per request and Postgres row locks suffice.
- **External security assessment.** Trigger: first paying household. The threat model's honest "No" rows are the scope.
- **Two-person activation for constitution changes.** Trigger: a household asks for it. An approval workflow overlay on activation, same pattern as approvals.
