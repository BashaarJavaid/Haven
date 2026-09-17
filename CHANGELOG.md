# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases use
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- 2026-09-15: Project architecture, threat model, roadmap, constitution spec, tool
  catalog, twin and scenario spec, demo script, submission checklist, and ADRs 001–008.
  No code yet; Phase 0 is next.
- 2026-09-16: Identity on a shared device: roles bind to linked accounts, never to voices;
  `security.*` classes are never approvable by voice (`ask_channels` must exclude `alexa`,
  validator-enforced); `requester.surface` condition attribute; reserved `requested_by.speaker`
  hook that can only lower authority; demo and scenario approve the unlock in the companion app.
- 2026-09-16: Positioning relative to the field: README "Why" and "What Haven adds" (constitution
  compiled to Cedar and enforced twice, planner over real prices, multi-member provenance,
  verification from the household's records) replace the "four innovations" table; the Devpost
  description draft and the demo thesis line lead with the same four. No build scope changed.
- 2026-09-16: Ring framing and gate: Ring is an event and media source only (its Partner API has no
  lock capability); the unlock is the devices adapter's lock, said so in the demo script, the Devpost
  draft, and the architecture. Roadmap item 34 now starts with a sandbox access gate (signed synthetic
  `button_press` received without a physical device); the Ring track entry is kept only if it passes,
  and dropping it leaves the Alexa+ entry and the twin doorbell untouched. Linking wording corrected
  from OAuth to Ring-driven app-integration linking.
- 2026-09-16: Boundary enforcement made literally true: the local stage-7 evaluator and the
  conformance test use the open-source Dogwood CLI (one evaluator, real temporal semantics; no
  hand-written shim; `cedarpy` kept only as a documented fallback); the compiler emits one generic
  temporal permit per approval TTL instead of one per `ask` class, so the 25-policy quota no longer
  limits constitution size; automated-reasoning analysis is stated as AWS-mode (AgentCore
  `validationMode`) with local activation recording "not analyzed"; the threat-model row for
  boundary divergence and ADR-003 now say the boundary is independent about policy, not context
  facts. Roadmap item 7 gains an early Dogwood gate; item 37 verifies analysis refusal.
- 2026-09-16: Core split into two roles of one image (ADR-008): `mcp` on AgentCore Runtime (MCP
  server, pipeline stages 1–6, never calls the Gateway or an adapter) and `worker` on one small
  always-on App Runner service (scheduler, pollers, HA WebSocket, Executor with stage 7 via the
  Gateway, companion API, Ring webhooks, web push), approved by the author. "Act" tools now return
  `status: executing` and the worker executes within seconds, so no tool call waits on the Gateway
  or a third-party network. The tick Lambda targets the worker. Runtime cold start is measured and
  reported separately from the warm latency budget. Roadmap items 19, 36, 38 and `haven doctor
  --aws` updated; friction-log candidate added.
- 2026-09-16: Savings numbers made defensible (option A: stay on ComEd real-time pricing). The
  demo assertion range is now provisional ($0.50–$3.00) until roadmap item 17 derives it from at
  least two weeks of recorded ComEd data run through the planner, with the derivation kept in
  `scripts/`; `peak_kwh_avoided` leads the scorecard and the plan summary; README dialogue, the
  Plan example, and the demo script no longer carry typed dollar figures; item 40 requires every
  figure in the video, README, and Devpost text to come from the cited run. The budget worked
  example now describes spend, not savings.
- 2026-09-16: Smaller-things batch. Threat model: every unearned row now reads Planned with its
  phase and eventual value. Constitution: overrides may only tighten (validator rule). Tool catalog
  merged from twenty-three to eleven tools with no capability dropped; all cross-references updated;
  a tool-selection test added to roadmap item 25. Emulator default is Claude Haiku 4.5 with Nova
  Lite selectable and the banner naming the model (ADR-007 revised). One web app (`apps/web`) with
  the simulator as a route replaces two apps; the MCP App bundle stays separate. Source labels are
  now `real`, `real API, demo devices`, `twin`; one physical energy-monitoring smart plug is the
  living-room light (bound via `asset_bindings`, twin fallback), lit at 18:55 for Mom's arrival and
  asserted in the scenario. Submission enters both mini-challenges with an upstream PR planned.
- 2026-09-16: Demo script restructured so each beat proves one thing. The scam beat is now the
  household's own request to send money, refused under `finance.transfer_money: never` and then
  verified through Dad's app (no relayed phone call). The overnight dishwasher, which the household's
  `appliance_start` rule makes an ASK after 22:00, is approved by voice at 23:30 and becomes the spine
  of the video (rule shown at 0:45, asks at 1:55, Cedar at 2:20); this also fixes the script
  contradicting the constitution. Wearable line and AWS console tour cut from the video only;
  console screenshots move to the Devpost gallery. Scenario timeline and assertions updated.
