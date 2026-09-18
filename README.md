# Hirz

**House rules for the AI in your home, and your parents'.**

Hirz lets your family decide what Alexa may do on its own, what it must ask about, and what it may never do. It holds a shared model of the people, devices, schedules, energy, and trust relationships in a home, plans against household goals instead of one-off commands, and acts only inside boundaries the household wrote down. The name for that in the architecture docs is *bounded autonomy*.

> Built for the **Build, Ship, Shape: Amazon Developer Hackathon 2026**: Alexa+ track, Ring track (kept only if the Ring sandbox access gate in `ROADMAP.md` item 34 passes), and both mini-challenges, AWS Builder and Open Source. Designed as a startup, not a weekend project: see [`ROADMAP.md`](./ROADMAP.md) for the hackathon cut line and what comes after it.

---

## Who it's for

The family's household manager: the adult who set up the smart home at their own place and at their parents' place, and who carries the worry for both.

- People reported losing **$3.5 billion to imposter scams in 2025**, nearly one in three fraud reports, and nearly three times the 2020 figure ([FTC, 2026-06-15](https://www.ftc.gov/news-events/news/press-releases/2026/06/ftc-data-show-people-reported-losing-3-point-5-billion-imposter-scams-2025)).
- Fraud losses reported by adults 60 and over rose about fourfold, from about $600 million in 2020 to **$2.4 billion in 2024**, driven largely by losses over $100,000, often to investment scams, romance scams, or impersonations ([FTC, *Protecting Older Consumers 2024–2025*](https://www.ftc.gov/news-events/news/press-releases/2025/12/ftc-issues-annual-report-congress-agencys-actions-protect-older-adults)).
- **63 million Americans**, about one in four adults, are family caregivers ([AARP and the National Alliance for Caregiving, *Caregiving in the U.S. 2025*](https://www.aarp.org/press/releases/2025-07-24-new-report-reveals-crisis-point-for-americas-63-million-family-caregivers.html)).

An assistant that can unlock doors and change the thermostat while someone sleeps, in a home you are responsible for but do not live in, needs rules you can read and proof they held. Hirz is **rules, not care**: it does not do medication or health monitoring. It gives that person autonomy inside a boundary at home, and protection at their parents'. It also does not stop scam calls. It gives Mom one simple thing to do: *ask first*.

## What it does

5:05 PM, at Mom's.

> **Mom:** Alexa, Malik just called from a strange number. He says he's in trouble and needs five hundred dollars. Is it really him?
>
> **Alexa (Hirz):** This looks like a family-impersonation scam. Don't send anything yet. I'm checking with Malik on his own phone. Ask me again in a minute.

Malik's phone buzzes: *"Your mom is checking it's really you. Did you just call her from another number asking for $500?"* He taps **No, that wasn't me.** The card on Mom's Echo Show moves from *checking with Malik* to the answer. Alexa cannot speak unprompted, so Mom asks.

> **Mom:** Alexa, is it him?
>
> **Alexa (Hirz):** Malik says that wasn't him. Don't send anything.

Hirz never used anything the caller said as a fact, and it never claimed to know the caller's number: it cannot see the call, and Mom did not read the number out. It asked Malik, about this specific request, through a channel the family verified in advance.

5:31 PM, at Malik's. He is just home, and rattled.

> **Malik:** Alexa, from now on, never unlock the door for someone we're not expecting.
>
> **Alexa (Hirz):** I've written that as a rule and sent it to your phone. It won't take effect until you approve it there.

On his phone: one English sentence, what changes in concrete situations (*Unexpected visitor: ask on phone → never. Expected arrival: still asks on your phone. Hirz does not identify the visitor.*), the compiled policy underneath. Those lines are computed by running the old and the new rules over a fixed set of situations; no model writes them. He activates it with his passkey. Anyone in the room can propose a rule. Only a person on their own phone can activate one.

> **Malik:** What's going on tonight?
>
> **Alexa (Hirz):** You're in the peak window until 7. I'll run the house off the battery, warm the living room for your mom, and hold the car until after 9.

The screen shows the plan as a card: what it saves tonight, three rows, one Approve button. He changes it by voice ("don't charge the car past 50, I'm not driving tomorrow"). Alexa confirms the constraint at once ("Got it, the car stops at 50. I'm updating the plan."), the card refreshes when the new plan lands a moment later, and only then does he say "do it". Hirz never lets him approve a plan that is still being recomputed.

At 6:40 the doorbell rings and nobody is expected. "Let them in."

> **Alexa (Hirz):** You added a rule tonight: I never unlock for someone who isn't expected.

At 7:04 it rings again. A vehicle pulled in at 6:58, and Mom is expected at 7:00. "That's my mom, let her in."

> **Alexa (Hirz):** Unlocking the door needs your approval on your phone. I've sent it.

The phone does not say "unlock for Mom". It says *"Someone is at the front door. Mom is expected now. Unlock for 10 minutes?"* A schedule is context, not identity: Malik is the one who confirms who is there.

Same lock, two outcomes. *Never*, because the family said so an hour ago. *Ask*, on a phone, never by voice, because an Echo is a shared device and Alexa does not tell add-ons who is speaking.

Every one of those sentences is backed by a structured record: what Hirz did, why, under which rule of the household constitution, at what risk band, and who approved it. Every number Hirz speaks comes from a cited scenario run. The demo household is on ComEd's published Time-of-Day rate, where the all-in peak price is several times the overnight price; the same evening is also run on ComEd's live hourly feed, and the backtest table below shows both. Nothing here is typed by hand.

The headline saving is measured against what a careful household already does: the car on a timer after 9 PM, the battery on its default self-consumption mode, the dishwasher on delay start. "Do everything now" and a simple cheapest-slots strategy are shown beside it. Every strategy delivers the same comfort, the same energy into the car, and ends with the battery no emptier than it started. On Hourly Pricing the backtest decides with the prices that were knowable at the time and is billed at the prices that actually happened. It also runs a home with a car and no solar or battery, and it reports the days on which Hirz adds little.

| Rate plan (both real ComEd residential rates) | Household | Saving per night vs. timer schedule (median, 10th–90th percentile) | vs. do everything now | Annualized vs. timer | Worst spike night avoided | Hours charged at negative prices |
|---|---|---|---|---|---|---|
| Time-of-Day (published rate table) | solar + battery + car | *from the backtest, `ROADMAP.md` item 17* | | | n/a | n/a |
| Time-of-Day | car only | | | | n/a | n/a |
| Hourly Pricing (live feed, a year of history) | solar + battery + car | | | | | |
| Hourly Pricing | car only | | | | | |

Time-of-Day's full supply-plus-delivery rate began on 2026-07-23, so a year-long replay on it is a counterfactual simulation and is labeled as one.

## Why existing agents fall short

Alexa+ can now call third-party tools over MCP, orchestrate multi-turn conversations, and render interactive UI. Household agents built on it already follow a common pattern: an allowlist of actions, a human-approval step for the risky ones, and an audit trail. That pattern is necessary and Hirz has it. It is not sufficient, for three reasons:

1. **The boundary is the developer's, not the household's.** An allowlist is written in code by whoever built the agent. A family needs to *write* the answer to "how much authority do you have?" themselves, change it, and see proof that it was enforced somewhere the agent's own code cannot get around.
2. **Trust comes from the caller.** The same channel that takes "turn off the lights" also takes "it's me, I'm in trouble, send money". An assistant with no record of who Malik is and how to reach him can only take the caller's word for it.
3. **One user, one command at a time.** Preferences, routines, people, assets, and constraints live in ten apps and nobody's head. Energy optimizers exist (EMHASS schedules solar, a battery, and deferrable loads for Home Assistant, and Home Assistant lets a household choose which devices an assistant can see). What they do not carry is the household: whose constraint moved the dishwasher, which written rule let the battery discharge, who approved the unlock, and proof that the limit held. Hirz's claim is that combination: household-authored permissions governing coordinated automation, with authenticated exceptions and evidence of enforcement.

## What Hirz adds

Approval gates, an audit ledger, and a simulated Alexa+ host are the baseline for a household agent, and Hirz has all three. The four things below are what Hirz adds on top of that baseline.

| | What it is | Why it matters |
|---|---|---|
| **A boundary the household writes, that the home itself enforces** | A Household Constitution, proposed by voice or written as a form, as YAML, or in plain English, and always activated by a person on their own phone. It states per action class and per member what Hirz may do on its own, what it must ask about, and what it may never do. Every version compiles to a Cedar/Dogwood policy set that AgentCore Policy enforces at the AWS tool boundary, including a temporal "approval must precede action" rule. Only a permit gets a command signed, and the home-side agent, Hirz Link, obeys only signed commands. | The boundary belongs to the family, not the developer. Hirz's own processes hold no credential that can act on a device; only commands the policy engine authorized are signed, and the home obeys only signed commands, once each, addressed to that home. This covers a bug or a bypass path in Hirz's own code. It does not yet cover a fully compromised worker, which could still tell the boundary an approval happened; closing that for security actions (the passkey itself verified at the boundary) is `ROADMAP.md` item 38d, and `THREAT_MODEL.md` says No until it is built. |
| **Verification from the household's own records** | Trusted contacts have channels verified out of band at setup. A request is checked against those records and confirmed through the subject's own app or verified number, never through anything the caller supplied. A recent scam call plus an unexpected visitor at the door raises a warning. Hirz has no way to move money, by design. | "Is this really Malik?" is answered by the graph, not by the person asking. |
| **A real planner over real prices** | A rolling-horizon MILP schedules the EV, the home battery, HVAC, and appliances against the household's real rate plan (all-in, supply plus delivery) and live weather, per-occupant comfort bands, and member constraints, and reports savings against a timer schedule a careful household would already use, with "do everything now" and a cheapest-slots strategy beside it, all held to the same comfort and delivered energy. A physics twin supplies every device that is not real, labeled as simulated. | The savings on the scorecard are computed, not typed, and the binding constraints and rejected alternatives are outputs of the model rather than a story about it. |
| **Multi-member coordination with provenance** | Each constraint and preference keeps the linked account it arrived on, the surface, and the time: "Dad, 22:40: kitchen in use until 23:00" survives into the plan, the explanation, and the audit row. Alexa does not say who spoke, so provenance is the account, never the voice; a name someone merely claims is recorded as claimed. Conflicts between members are returned as data with the people involved, never silently resolved. | A household is not one user. The plan can say whose request moved the dishwasher, and why. |

Underneath all four: a deterministic risk engine whose bands set floors the constitution can tighten but never loosen, and a pipeline in which every action carries what, why, which rule, and what was rejected, as data that Alexa narrates. Those are the mechanisms that make the four hold; they are not the claim.

In local mode there is no outside boundary: the second policy evaluator runs in the same container and is labeled as exactly that. "Enforced outside Hirz" is claimed for the AWS deployment only.

**What the rules cover.** Hirz governs the actions Hirz takes. A lock that is also linked to Alexa directly, exposed to an assistant by Home Assistant, or opened with the vendor's app or a key has a path that does not pass through Hirz, and Hirz cannot refuse what it never sees. The deployment rule is that a device Hirz governs is not exposed to Alexa by another route; the Household page shows each device as *managed through Hirz* or *not managed*; and when a governed device changes state without a command from Hirz, that is recorded as *changed outside Hirz* and, for locks and cameras, the owner is told. A manual thermostat change is respected for a while rather than overwritten. `THREAT_MODEL.md` has the row.

## Architecture

![Hirz loop](./docs/img/loop.svg)

*Observe → Understand → Plan → Evaluate Risk → Check Authority → Act → Verify → Remember. Every action Hirz takes passes through that loop, and every step of it is recorded.*

Every box is a module described in [`ARCHITECTURE.md`](./ARCHITECTURE.md). Surfaces talk to Hirz Core only through MCP tools or the companion API; Core talks to the world only through adapters, each of which has a real implementation and a **digital-twin** implementation behind the same interface.

```mermaid
graph TD
    subgraph Surfaces
        Alexa["Alexa+ (MCP add-on, Streamable HTTP, MCP App UI)"]
        Sim["Hirz Simulator (web: emulated Alexa+ host, voice + screen)"]
        App["Companion web app (constitution, approvals, audit, twin)"]
    end

    Alexa --> MCP["MCP Server + OAuth 2.1 (PRM, PKCE)"]
    Sim --> MCP
    App --> API["Companion API"]

    subgraph Core["Hirz Core (Python)"]
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
        Dev["Devices: Home Assistant, reached through Hirz Link (home agent: holds the token, obeys only signed commands)"]
        EV["EV: Smartcar sandbox / Tesla / twin"]
        Energy["Energy: ComEd Time-of-Day rate table + Hourly feed, Open-Meteo, battery + solar twin"]
        Wear["Wearable: Oura / Whoop / Bee / twin"]
        Cal["Calendar: Google / ICS / twin"]
        Door["Doorbell: Ring sandbox / twin"]
        Notify["Notifications: web push, email"]
    end
    Exec --> Adapters
    Ctx --> Adapters
    Twin["Digital Twin + Scenario Engine (thermal, battery, EV, solar, occupancy, events, sim clock)"] -.-> Adapters

    subgraph AWS["AWS (AgentCore + Bedrock)"]
        RT["AgentCore Runtime (hosts the MCP server role)"]
        WK["Worker service (App Runner: scheduler, executor, pollers, Link relay, companion API, webhooks; holds no device credential)"]
        GW["AgentCore Gateway + Policy (Cedar compiled from the constitution, temporal approval rules)"]
        KMS["KMS key: only the Gateway's Lambda may sign a home command"]
        S3A["S3 Object Lock: audit chain anchors"]
        Mem["AgentCore Memory"]
        Id["AgentCore Identity (outbound credential vault)"]
        BR["Bedrock: Claude Haiku 4.5 / Sonnet 5; emulator on Haiku 4.5 by default, Nova Lite selectable"]
        Sched["EventBridge Scheduler + Lambda ticks"]
    end
    MCP -.-> RT
    Exec -.-> WK
    API -.-> WK
    Exec -.-> GW
    GW -.-> KMS
    Audit -.-> S3A
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
8. → EXECUTE | ASK | DENY | VERIFY    (EXECUTE on a home device = a command the boundary signed, verified in the home)
```

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Core | Python 3.12, FastAPI, official `mcp` SDK (FastMCP), async throughout | First-party MCP SDK; same stack as the author's prior MCP work; AgentCore Runtime's MCP contract is Python-first |
| Planner | `scipy.optimize.milp` (HiGHS) rolling-horizon scheduler | Deterministic, explainable, one dependency; no LLM in the optimization loop ([ADR-005](./docs/adr/ADR-005-deterministic-planner.md)) |
| Policy | YAML constitution + Pydantic schema + a non-Turing-complete condition grammar, compiled to Cedar | Git-diffable, validated at load, analyzable; enforced in-process and at the AWS tool boundary ([ADR-003](./docs/adr/ADR-003-constitution-yaml-to-cedar.md)) |
| Risk | Fixed action-class table + dynamic factors, **no ML** | A household decision the family can't explain is one they can't trust ([ADR-004](./docs/adr/ADR-004-no-ml-risk-scoring.md)) |
| Storage | PostgreSQL 16 (household graph, constitution versions, plans, approvals, audit chain) + AgentCore Memory (conversational, preference extraction) | Relational integrity for a hash chain; graph as tables + JSONB ([ADR-002](./docs/adr/ADR-002-postgres-over-dynamodb.md)) |
| Surfaces | React + TypeScript: MCP App cards (`@modelcontextprotocol/ext-apps`, plain CSS carrying Amazon's design tokens), companion app and simulator (Tailwind + shadcn/ui) | The MCP Apps SDK and the Alexa tooling are TypeScript ([ADR-001](./docs/adr/ADR-001-python-core-typescript-surfaces.md)); the cards follow Amazon's add-on design guide verbatim ([`docs/design.md`](./docs/design.md)) |
| Home agent | Hirz Link: a small Python process beside Home Assistant, outbound-only, executes only KMS-signed commands | The Home Assistant token never leaves the house, no tunnel, and a bypass in Hirz's own processes has nothing to act with ([ADR-009](./docs/adr/ADR-009-signed-commands-home-agent.md)) |
| Open source | A separate repository: an add-on conformance checker (CLI, black-box against any MCP server) and the simulator's generic host harness | Add-on developer access is limited to select partners, so builders test against emulated hosts; the checker tells any of them in one command whether a server meets Amazon's published contract. Hirz's simulator is built on the published harness and its CI runs the checker |
| Alexa+ | MCP 2025-11-25, Streamable HTTP, OAuth 2.1 + PKCE S256, Protected Resource Metadata, MCP Apps for visuals | The add-on contract, verbatim ([ADR-007](./docs/adr/ADR-007-alexa-surface-strategy.md)) |
| AWS | AgentCore Runtime, Gateway, Policy, Memory, Identity; Bedrock (Claude Haiku 4.5 / Sonnet 5; the emulator runs Haiku 4.5 by default with Nova Lite selectable); EventBridge Scheduler + Lambda; KMS (command signing); S3 Object Lock (audit anchors); CDK (TypeScript) | AWS runs Hirz's agentic state and enforcement, not just its hosting ([ADR-008](./docs/adr/ADR-008-agentcore-topology.md)) |
| Twin | Physics-lite models with a simulated clock and a YAML scenario DSL | Everything is demonstrable end to end with no hardware, and every scenario is an integration test ([ADR-006](./docs/adr/ADR-006-twin-first-adapters.md)) |
| Ops | Docker Compose (Postgres, Home Assistant demo, Hirz), OpenTelemetry → CloudWatch via AgentCore Observability, GitHub Actions (ruff / mypy strict / pytest 80% gate / tsc / vitest / playwright) | |

## Repository layout

```
Hirz/
├── README.md, ARCHITECTURE.md, THREAT_MODEL.md, ROADMAP.md, SECURITY.md, CHANGELOG.md
├── CLAUDE.md, AGENTS.md            # instruction files for coding agents (kept at parity)
├── docs/
│   ├── adr/                        # one file per consequential decision
│   ├── constitution.md             # the Household Constitution spec
│   ├── tool-catalog.md             # every MCP tool: name, schema, output, voice fallback
│   ├── twin-and-scenarios.md       # digital twin models and the scenario DSL
│   ├── design.md                   # Amazon's design tokens, per-card specs, the seven hand-designed screens
│   ├── demo-script.md              # the 3-minute video, beat by beat
│   └── submission.md               # hackathon requirements checklist
├── hirz/                          # Python core package
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
│   ├── link/                       # Hirz Link: the home agent that obeys only signed commands
│   ├── mcp/                        # MCP server, tools, OAuth PRM, MCP App resources
│   ├── api/                        # companion API (FastAPI)
│   └── cli.py                      # hirz CLI: decide, plan, scenario, verify-audit, doctor
├── apps/
│   ├── mcp-app/                    # React MCP App bundle (plan card, approval card, verification card, scorecard)
│   └── web/                        # one React app: companion pages + the Alexa+ simulator route (emulator agent, voice, device modes)
├── infra/cdk/                      # AWS CDK (TypeScript): AgentCore, Cognito, Bedrock access, scheduler, RDS
├── scenarios/                      # YAML scenarios (the parents' scam check, the demo evening, test fixtures)
├── constitutions/                  # quinn-home (Malik's), quinn-parents (Mom and Dad's), examples
├── tariffs/                        # published rate tables with source URLs (ComEd Time-of-Day)
├── compose.dev.yml, compose.demo.yml, compose.link.yml
├── alembic/                        # Postgres migrations
├── scripts/
└── tests/{unit,integration,adversarial,scenarios,ux,latency}
```

## Scaffold setup (Phase 0, items 1–2)

The Python package has a liveness endpoint and local-development bootstrap checks.
The `web` and `mcp-app` workspaces still contain import smoke tests only. There is
no household application behavior or Hirz CLI yet.

Verified toolchain: Python **3.12.13**, uv **0.12.15**, Node **24.21.0**, and pnpm
**12.4.2**. Python is selected by `.python-version`; pnpm is recorded in
`package.json`. Direct dependencies are pinned exactly, with both lockfiles checked in.

On macOS with Homebrew, install the tools and select Node 24 for this shell only
(Homebrew installs its currently available versions):

```bash
brew install uv pnpm node@24
export PATH="$(brew --prefix node@24)/bin:$PATH"
```

From the repository root:

```bash
uv sync --locked
pnpm install --frozen-lockfile
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy hirz/ scripts/
pnpm -r lint
pnpm -r typecheck
pnpm -r test
uv build
```

Python tests cover package metadata, liveness, and bootstrap credential/protocol
handling. Each TypeScript workspace tests its empty module import. Python enforces
**80% line coverage over `hirz/`**; the liveness endpoint is only five executable
statements, so 100% is not evidence of household application behavior. The bootstrap
scripts have separate behavioral tests. No cloud credentials, Docker services, or
browser are needed for these tests; the WebSocket test binds a temporary local port.

## Local development stack (Phase 0, item 2)

Start Docker before running these commands from the repository root:

```bash
uv sync --locked
uv run python scripts/init_dev.py
docker compose -f compose.dev.yml up -d
uv run python scripts/check_dev.py
```

The initializer creates missing local credentials in ignored `.env` (mode `0600`),
starts Postgres and Home Assistant, completes HA onboarding, and saves a 365-day
long-lived token. It preserves existing credentials and unrelated `.env` entries;
rerunning it reuses a valid token. Do not run initializers concurrently. Initial
image downloads can take several minutes; readiness waits are bounded to 180 seconds.
Use `.env` for these credentials, not competing shell environment variables.

| Service | Address | What exists now |
|---|---|---|
| Hirz | <http://localhost:8000/health> | `200 {"status":"ok"}`; process liveness only |
| Home Assistant | <http://localhost:8123> | Real API, demo devices (**simulated**) |
| PostgreSQL | `localhost:5432` | Database/user `hirz`; no application schema yet |
| Jaeger, optional | <http://localhost:16686> | In-memory traces; no Hirz instrumentation yet |

All published ports bind to `127.0.0.1`. Hirz has no `/ready`, MCP, API docs, worker,
or companion pages yet. Its runtime contains no device credentials. The development
container sets `HIRZ_LLM=off` and needs no AWS account. HA uses “Hirz Demo,” English,
`America/Chicago`, US customary units, username `hirz`, and display name “Hirz Developer.”
Retrieve the generated password privately from `.env` to sign into HA.

HA's unmodified demo integration supplies the entities; the checker requires
`climate.ecobee`, `cover.garage_door`, `light.bed_light`, and
`sensor.outside_temperature`. Native onboarding also initializes `google_translate`,
`met`, `radio_browser`, and `shopping_list`, plus frontend dependencies. Analytics
sharing stays off. These are demo infrastructure, not household actions; neither
script calls device services or substitutes for the future decision pipeline.

HA's [installation guide](https://www.home-assistant.io/installation/linux/)
excludes Docker Desktop from its supported Container setup. This demo-only stack
passed on macOS ARM64 with Docker Desktop **4.87.0**, Engine **29.7.2**, and Compose
**5.4.0** on **2026-09-17**; it does not establish physical-device support.
If it fails on your runtime, retain the volumes and investigate before switching
runtimes. No host networking, privileged mode, or physical-device mounts are used.

For the roadmap's direct authenticated API check, pass the header through stdin
so the token is absent from curl's command-line arguments:

```bash
uv run python -c 'from dotenv import dotenv_values; print("Authorization: Bearer " + dotenv_values(".env", interpolate=False)["HA_TOKEN"])' \
  | curl --fail --silent --show-error --header @- http://localhost:8123/api/states
```

The response contains demo entities. Without that header, HA returns `401`.
`check_dev.py` additionally checks a password-authenticated Postgres query and Hirz
liveness; it prints entity IDs and results, never credentials.

```bash
# Rebuild after Python source/dependency changes; no source mount or reload watcher.
docker compose -f compose.dev.yml up -d --build

# Optional Jaeger; OTLP ports 4317/4318 remain internal to Compose.
docker compose -f compose.dev.yml --profile observability up -d
uv run python scripts/check_dev.py --observability

# Stop all services, retaining Postgres and HA named volumes and .env.
docker compose -f compose.dev.yml --profile observability down
```

The observability check submits one disposable `hirz-dev-check` trace from inside
the Compose network and retrieves it by ID. Jaeger stores traces in memory and
loses them on restart. No tracing SDK is installed in Hirz.

**Recovery:** if HA is already onboarded and `HA_TOKEN` is absent, invalid, or
expired, sign into HA with the original credentials, finish any pending onboarding,
then create a replacement under **Profile → Security → Long-lived access tokens**.
Revoke an obsolete “Hirz local development” token before reusing its name. Save the
replacement as `HA_TOKEN` in `.env` and rerun initialization. The script does not
automatically sign in again or edit HA authentication storage. Missing credentials
for existing volumes require restoring the original `.env`; changing the Postgres
environment variable does not change a persisted database password. Inspect service
status with `docker compose -f compose.dev.yml ps`; do not publish `.env`, rendered
Compose configuration, or container inspection output containing credentials.

**Destructive reset, only when intentionally discarding this demo's data:**

```bash
docker compose -f compose.dev.yml --profile observability down --volumes
```

This deletes both the database and HA state. Remove only `HA_TOKEN` from `.env`
(preserving unrelated entries), then rerun the first-start commands. Ordinary
shutdown uses `down` without `--volumes`. Never use this reset to recover a token.

## Quickstart (target state, see `ROADMAP.md` Phase 0)

```bash
git clone https://github.com/BashaarJavaid/Hirz && cd Hirz
uv sync --locked
uv run python scripts/init_dev.py
docker compose -f compose.dev.yml up -d          # Postgres 16 + Home Assistant (demo devices) + Hirz
uv sync && uv run alembic upgrade head
uv run hirz scenario run scenarios/demo-evening.yaml --speed 60   # the whole evening in 3 minutes
open http://localhost:3000                       # companion app + simulator
```

During the judging window there is also a hosted demo: one click seeds a throwaway household on simulated devices only, so nothing needs installing (the link is in the Devpost testing instructions). No AWS account is required for the local path. `HIRZ_LLM=off` runs every flow deterministically with canned explanations, which is what CI uses and what a judge with no credentials can run.

## Documentation

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — layers, the decision pipeline, canonical objects, every component in depth, data model, latency budget, failure modes, hardening, observability, testing, CI/CD, deployment
- [`THREAT_MODEL.md`](./THREAT_MODEL.md) — what Hirz protects against, what it doesn't, and the assumptions underneath
- [`docs/constitution.md`](./docs/constitution.md) — the Household Constitution: schema, modes, conditions, compilation to Cedar, examples
- [`docs/tool-catalog.md`](./docs/tool-catalog.md) — the MCP tool surface Alexa+ sees
- [`docs/twin-and-scenarios.md`](./docs/twin-and-scenarios.md) — the digital twin and scenario DSL
- [`docs/design.md`](./docs/design.md) — the visual design spec: Amazon's tokens, display modes, per-card specs
- [`docs/demo-script.md`](./docs/demo-script.md) — the video storyboard
- [`docs/submission.md`](./docs/submission.md) — hackathon checklist and the product-feedback / friction-log plan
- [`docs/adr/`](./docs/adr/) — decisions and rejected alternatives
- [`ROADMAP.md`](./ROADMAP.md) — build order as a living checklist, with the hackathon cut line
- [`SECURITY.md`](./SECURITY.md) — disclosure policy

## How this is built

Hirz is built by one engineer working with AI coding assistants. The design decisions are the human's: the thesis, the four things Hirz adds, the decision pipeline and its precedence, the fail-closed posture, the choice to keep the risk engine free of ML and the constitution non-Turing-complete, the twin-first adapter strategy, and every rejected alternative in `docs/adr/`. The assistants implement downstream of those decisions under the standing rules in [`CLAUDE.md`](./CLAUDE.md): surface assumptions, ask before deciding, no speculative complexity, verify every feature by running it.

Nothing in this README is asserted on a model's say-so. Where something is simulated it is labeled as a twin in the UI and in the docs. Where something is unproven or unprotected, `THREAT_MODEL.md` says so.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
