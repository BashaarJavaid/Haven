# Haven

**The bounded-autonomy operating system for the home.** Haven turns Alexa+ from a command-driven assistant into a permissioned household agent: it holds a shared model of the people, devices, schedules, energy, and trust relationships in a home, plans against household goals instead of one-off commands, and acts only inside boundaries the household wrote down.

![Haven loop](./docs/img/loop.svg)

*Observe → Understand → Plan → Evaluate Risk → Check Authority → Act → Verify → Remember. Every action Haven takes passes through that loop, and every step of it is recorded.*

> Built for the **Build, Ship, Shape: Amazon Developer Hackathon 2026** — Alexa+ track (primary), Ring track (secondary), AWS Builder mini-challenge. Designed as a startup, not a weekend project: see [`ROADMAP.md`](./ROADMAP.md) for the hackathon cut line and what comes after it.

---

## Why

Today's smart home follows commands. You say "set the thermostat to 72", "charge the car", "remind Mom about her pills", "add milk". The assistant executes each one in isolation. It has no model of who lives in the house, what they need tonight, what electricity costs at 6 PM, which requests are normal and which are dangerous, or how much authority it has been given.

Alexa+ can now call third-party tools over MCP, orchestrate multi-turn conversations, and render interactive UI. What it cannot do is *understand the household as a whole*, because no shared household model exists for it to reason over. Three concrete gaps:

1. **No household model.** Preferences, routines, people, assets, and constraints live in ten apps and nobody's head. The assistant can't plan across them.
2. **No permission boundary.** An agent that can unlock doors, move money, and change the thermostat while someone sleeps needs an explicit, user-authored answer to "how much authority do you have?" Nothing today provides one.
3. **No protection posture.** The same channel that takes "turn off the lights" also takes "Dad's stranded, send money to this number". Nothing distinguishes a routine request from a high-risk one, or verifies identity from a trusted record instead of from the caller.

Haven closes all three with one thesis: **bounded autonomy**. Understand the household, negotiate competing needs, take safe autonomous action, and know when to ask.

## What it does

You get home at 5:30 PM.

> **You:** Alexa, what's going on tonight?
>
> **Alexa (Haven):** You're home earlier than usual. Your parents are coming at 7, the car is at 34 percent, and electricity prices spike at 6. I can pre-warm the living room for your mom, charge the home battery before prices rise, hold the car until the cheap window after midnight, and have everything ready by 7. Estimated savings tonight: about six dollars.

The screen shows the plan as a card: each action, when, why, and the numbers. You approve it, or change it by voice ("I'm not driving tomorrow, 50 percent is fine"), and the plan re-optimizes.

At 6:15 the phone rings.

> **You:** Alexa, Dad just called from a new number. He says he's stranded and needs me to send money to a friend.
>
> **Alexa (Haven):** That number isn't one of Dad's verified contacts, and the request combines urgency, money, and a new channel, which is the pattern of a family impersonation scam. Before anything else, I've sent a check-in to Dad's own Haven app and can call his verified number. Want me to?

Dad taps "I'm fine" on his phone. Haven never used anything the caller said as a fact.

Next morning:

> **Alexa (Haven):** Good morning. Overnight I charged the car to 52 percent in the 1 AM window, ran the dishwasher after your dad finished in the kitchen, and kept the house within your comfort band. Energy saved yesterday: eight dollars ten. One request was flagged and verified. Your recovery score is lower than usual and your first meeting is at 10, so your Recovery Morning preferences are ready if you want them.

Every one of those sentences is backed by a structured record: what Haven did, why, under which rule of the household constitution, at what risk band, and who approved it.

## The four innovations

| | What it is | Why it matters |
|---|---|---|
| **Household Graph** | A typed, versioned model of people, roles, trusted contacts, assets, devices, schedules, preferences, and policies. | Lets one agent reason *across* domains: Mom's temperature preference, the car's deadline, tonight's prices, and Dad's kitchen constraint in one plan. |
| **Household Constitution** | A user-authored document that states, per action class and per member, what Haven may do automatically, what it must ask about, and what it may never do. Authored as a form, as YAML, or in plain English. Compiled to Cedar and enforced twice: in Haven and at the AWS tool boundary. | Answers the question every agentic home has to answer and none do: how much authority does the AI have? |
| **Risk-adjusted autonomy** | Every proposed action is classified by impact, reversibility, and uncertainty into a risk band. The band sets a floor the constitution can tighten but never loosen. Low: act. Medium: constitution decides. High: ask. Critical: never act autonomously; verify. | Makes "safe autonomous action" a deterministic property of the system rather than a hope about the model. |
| **Explainable autonomy** | Every action carries what, why, which rule, what was considered and rejected, and what the outcome was, as data. Alexa narrates the data; Haven never scripts Alexa's speech. | This is what Alexa+ is built for, and it is what makes an audit trail a product feature rather than a compliance artifact. |

## Architecture

Every box is a module described in [`ARCHITECTURE.md`](./ARCHITECTURE.md). Surfaces talk to Haven Core only through MCP tools or the companion API; Core talks to the world only through adapters, each of which has a real implementation and a **digital-twin** implementation behind the same interface.

```mermaid
graph TD
    subgraph Surfaces
        Alexa["Alexa+ (MCP add-on, Streamable HTTP, MCP App UI)"]
        Sim["Haven Simulator (web: emulated Alexa+ host, voice + screen)"]
        App["Companion web app (constitution, approvals, audit, twin)"]
    end

    Alexa --> MCP["MCP Server + OAuth 2.1 (PRM, PKCE)"]
    Sim --> MCP
    App --> API["Companion API"]

    subgraph Core["Haven Core (Python)"]
        MCP --> Ctx["Context Service (Household Graph read model)"]
        MCP --> Pipe["Decision Pipeline"]
        API --> Pipe
        Pipe --> Risk["Risk Engine (deterministic bands)"]
        Pipe --> Const["Constitution Engine (allow / ask / never + conditions)"]
        Pipe --> Exec["Executor (idempotent actions, verify-after-act, scheduler)"]
        Planner["Planner (rolling-horizon MILP) + Coordinator (member constraints)"] --> Pipe
        Protect["Protect (trusted contacts, verification, request assessment)"] --> Pipe
        Exec --> Audit["Audit Ledger (hash-chained, signed)"]
        Pipe --> Audit
        Explain["Explainer (Bedrock Claude, structured facts → narration data)"]
        Memory["Memory (Postgres graph of record + AgentCore Memory)"]
    end

    subgraph Adapters["Adapters (real | twin)"]
        Dev["Devices: Home Assistant"]
        EV["EV: Smartcar sandbox / Tesla / twin"]
        Energy["Energy: ComEd prices, Open-Meteo, battery + solar twin"]
        Wear["Wearable: Oura / Whoop / Bee / twin"]
        Cal["Calendar: Google / ICS / twin"]
        Door["Doorbell: Ring sandbox / twin"]
        Notify["Notifications: web push, email"]
    end
    Exec --> Adapters
    Ctx --> Adapters
    Twin["Digital Twin + Scenario Engine (thermal, battery, EV, solar, occupancy, events, sim clock)"] -.-> Adapters

    subgraph AWS["AWS (AgentCore + Bedrock)"]
        RT["AgentCore Runtime (hosts MCP server)"]
        GW["AgentCore Gateway + Policy (Cedar compiled from the constitution, temporal approval rules)"]
        Mem["AgentCore Memory"]
        Id["AgentCore Identity (outbound credential vault)"]
        BR["Bedrock: Claude Haiku 4.5 / Sonnet 5, Nova Lite (emulator)"]
        Sched["EventBridge Scheduler + Lambda ticks"]
    end
    MCP -.-> RT
    Exec -.-> GW
    Memory -.-> Mem
    Adapters -.-> Id
    Explain -.-> BR
    Exec -.-> Sched
```

**The decision pipeline, in order.** A proposed action is resolved by one deterministic, ordered pipeline (full detail in `ARCHITECTURE.md` §3):

```
1. Identity + role resolution      → unknown requester → least authority
2. Constitution NEVER              → DENY (terminal)
3. Risk floor                      → CRITICAL → DENY or VERIFY (terminal)
4. Constitution mode + conditions  → auto | ask | never
5. Risk band escalation            → HIGH forces ASK even where the constitution says auto
6. Budgets and rate limits         → daily $ limit, action counts → ASK or DENY
7. Boundary enforcement (Cedar)    → AgentCore Policy must agree; disagreement fails closed
8. → EXECUTE | ASK | DENY | VERIFY
```

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Core | Python 3.12, FastAPI, official `mcp` SDK (FastMCP), async throughout | First-party MCP SDK; same stack as the author's prior MCP work; AgentCore Runtime's MCP contract is Python-first |
| Planner | `scipy.optimize.milp` (HiGHS) rolling-horizon scheduler | Deterministic, explainable, one dependency; no LLM in the optimization loop ([ADR-005](./docs/adr/ADR-005-deterministic-planner.md)) |
| Policy | YAML constitution + Pydantic schema + a non-Turing-complete condition grammar, compiled to Cedar | Git-diffable, validated at load, analyzable; enforced in-process and at the AWS tool boundary ([ADR-003](./docs/adr/ADR-003-constitution-yaml-to-cedar.md)) |
| Risk | Fixed action-class table + dynamic factors, **no ML** | A household decision the family can't explain is one they can't trust ([ADR-004](./docs/adr/ADR-004-no-ml-risk-scoring.md)) |
| Storage | PostgreSQL 16 (household graph, constitution versions, plans, approvals, audit chain) + AgentCore Memory (conversational, preference extraction) | Relational integrity for a hash chain; graph as tables + JSONB ([ADR-002](./docs/adr/ADR-002-postgres-over-dynamodb.md)) |
| Surfaces | React + TypeScript: MCP App (`@modelcontextprotocol/ext-apps`), companion app, simulator | The MCP Apps SDK and the Alexa tooling are TypeScript ([ADR-001](./docs/adr/ADR-001-python-core-typescript-surfaces.md)) |
| Alexa+ | MCP 2025-11-25, Streamable HTTP, OAuth 2.1 + PKCE S256, Protected Resource Metadata, MCP Apps for visuals | The add-on contract, verbatim ([ADR-007](./docs/adr/ADR-007-alexa-surface-strategy.md)) |
| AWS | AgentCore Runtime, Gateway, Policy, Memory, Identity; Bedrock (Claude Haiku 4.5 / Sonnet 5; Nova Lite for the emulator); EventBridge Scheduler + Lambda; CDK (TypeScript) | AWS runs Haven's agentic state and enforcement, not just its hosting ([ADR-008](./docs/adr/ADR-008-agentcore-topology.md)) |
| Twin | Physics-lite models with a simulated clock and a YAML scenario DSL | Everything is demonstrable end to end with no hardware, and every scenario is an integration test ([ADR-006](./docs/adr/ADR-006-twin-first-adapters.md)) |
| Ops | Docker Compose (Postgres, Home Assistant demo, Haven), OpenTelemetry → CloudWatch via AgentCore Observability, GitHub Actions (ruff / mypy strict / pytest 80% gate / tsc / vitest / playwright) | |

## Repository layout

```
Haven/
├── README.md, ARCHITECTURE.md, THREAT_MODEL.md, ROADMAP.md, SECURITY.md, CHANGELOG.md
├── CLAUDE.md, AGENTS.md            # instruction files for coding agents (kept at parity)
├── docs/
│   ├── adr/                        # one file per consequential decision
│   ├── constitution.md             # the Household Constitution spec
│   ├── tool-catalog.md             # every MCP tool: name, schema, output, voice fallback
│   ├── twin-and-scenarios.md       # digital twin models and the scenario DSL
│   ├── demo-script.md              # the 3-minute video, beat by beat
│   └── submission.md               # hackathon requirements checklist
├── haven/                          # Python core package
│   ├── graph/                      # household graph models, repository, versioning
│   ├── constitution/               # schema, loader, condition grammar, Cedar compiler, evaluator
│   ├── risk/                       # action classes, factors, bands
│   ├── pipeline/                   # the decision pipeline and the canonical Decision
│   ├── planner/                    # MILP scheduler, coordinator, plan diff
│   ├── executor/                   # action runtime, scheduler, verify-after-act
│   ├── protect/                    # trusted contacts, verification, request assessment
│   ├── explain/                    # Bedrock-backed explainer (structured in, structured out)
│   ├── audit/                      # hash chain, signing, export, verifier
│   ├── adapters/                   # one package per domain; each has real/ and twin/
│   ├── twin/                       # physics models, sim clock, scenario engine
│   ├── mcp/                        # MCP server, tools, OAuth PRM, MCP App resources
│   ├── api/                        # companion API (FastAPI)
│   └── cli.py                      # haven CLI: decide, plan, scenario, verify-audit, doctor
├── apps/
│   ├── mcp-app/                    # React MCP App (plan card, approval card, verification card, scorecard)
│   ├── companion/                  # React companion web app
│   └── simulator/                  # React Alexa+ simulator host (emulator agent, voice, device modes)
├── infra/cdk/                      # AWS CDK (TypeScript): AgentCore, Cognito, Bedrock access, scheduler, RDS
├── scenarios/                      # YAML scenarios (the demo evening, test fixtures)
├── constitutions/                  # example constitutions incl. the demo household
├── compose.dev.yml, compose.demo.yml
├── alembic/                        # Postgres migrations
├── scripts/
└── tests/{unit,integration,adversarial,scenarios,ux,latency}
```

## Quickstart (target state, see `ROADMAP.md` Phase 0)

```bash
git clone https://github.com/BashaarJavaid/HavenOS && cd HavenOS
cp .env.example .env
docker compose -f compose.dev.yml up -d          # Postgres 16 + Home Assistant (demo devices) + Haven
uv sync && uv run alembic upgrade head
uv run haven scenario run scenarios/demo-evening.yaml --speed 60   # the whole evening in 3 minutes
open http://localhost:3000                       # companion app + simulator
```

No AWS account is required for the local path. `HAVEN_LLM=off` runs every flow deterministically with canned explanations, which is what CI uses and what a judge with no credentials can run.

## Documentation

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — layers, the decision pipeline, canonical objects, every component in depth, data model, latency budget, failure modes, hardening, observability, testing, CI/CD, deployment
- [`THREAT_MODEL.md`](./THREAT_MODEL.md) — what Haven protects against, what it doesn't, and the assumptions underneath
- [`docs/constitution.md`](./docs/constitution.md) — the Household Constitution: schema, modes, conditions, compilation to Cedar, examples
- [`docs/tool-catalog.md`](./docs/tool-catalog.md) — the MCP tool surface Alexa+ sees
- [`docs/twin-and-scenarios.md`](./docs/twin-and-scenarios.md) — the digital twin and scenario DSL
- [`docs/demo-script.md`](./docs/demo-script.md) — the video storyboard
- [`docs/submission.md`](./docs/submission.md) — hackathon checklist and the product-feedback / friction-log plan
- [`docs/adr/`](./docs/adr/) — decisions and rejected alternatives
- [`ROADMAP.md`](./ROADMAP.md) — build order as a living checklist, with the hackathon cut line
- [`SECURITY.md`](./SECURITY.md) — disclosure policy

## How this is built

Haven is built by one engineer working with AI coding assistants. The design decisions are the human's: the thesis, the four innovations, the decision pipeline and its precedence, the fail-closed posture, the choice to keep the risk engine free of ML and the constitution non-Turing-complete, the twin-first adapter strategy, and every rejected alternative in `docs/adr/`. The assistants implement downstream of those decisions under the standing rules in [`CLAUDE.md`](./CLAUDE.md): surface assumptions, ask before deciding, no speculative complexity, verify every feature by running it.

Nothing in this README is asserted on a model's say-so. Where something is simulated it is labeled as a twin in the UI and in the docs. Where something is unproven or unprotected, `THREAT_MODEL.md` says so.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
