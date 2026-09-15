# MCP Tool Catalog

The tool surface Alexa+ (and the simulator) sees. Six groups, twenty-one tools. Every tool follows the same contract:

- **Input** is a JSON Schema 2020-12 `inputSchema` with every parameter described in consumer terms and with synonyms (Alexa+ resolves "the living room", "lounge", "front room" through the description).
- **Output** conforms to an `outputSchema` and always includes `speakable` (`headline`, `details[≤3]`, `options[≤5]`) so voice-only devices are complete, plus structured `data`, plus optional `ui` (an MCP App resource reference) for display devices.
- **Errors** are MCP tool-execution errors with a consumer-language `message` and a machine `code`; never protocol errors for validation problems, so the host can self-correct.
- **No internal IDs in speakable text.** Plan, action, and case ids travel in `data` and in `_meta` only.
- **Latency** under the §8 budget; nothing in a tool waits on a model, a solver, or a third-party network call.
- **Scopes** (OAuth): `haven:read`, `haven:plan`, `haven:act`, `haven:verify`. A token without the scope gets a friendly refusal, not a 401.

Naming follows the 2025-11-25 guidance: lowercase, underscores, verb first.

---

## Context

| Tool | Scope | Purpose |
|---|---|---|
| `what_can_you_do` | none | Returns a contextual capability summary ("Tonight I can plan energy, keep the house comfortable for your parents, and check suspicious requests"). Required by Alexa+'s onboarding rules; works for unlinked users with a generic summary. |
| `get_household_context` | read | The household right now: who is home and expected, current plan headline, energy state, active constraints, unusual situations. Input: optional `scope` (`people`, `energy`, `plan`, `security`, `all`). |
| `get_household_member` | read | A member's preferences, role, presence, and (if a trusted contact) verification status. Input: `member` (name or relationship; synonyms: "mom", "my mother", "Anita"). Never returns channel values, only whether they are verified. |
| `get_current_constraints` | read | Active constraints with provenance ("Dad: kitchen in use until 11 PM"). |
| `record_household_preference` | plan | Records a preference or constraint from the speaker: `text`, `applies_to` (member/asset/zone), `window` (optional), `kind` (`preference`, `constraint`, `one_time`). Triggers Coordinator normalization and, if it affects the plan, a re-plan. |

## Planning

| Tool | Scope | Purpose |
|---|---|---|
| `create_household_plan` | plan | Returns the current plan for a horizon (`tonight`, `overnight`, `tomorrow_morning`, `next_24h`) with goals honored, actions, numbers, alternatives, and the approval state. Fresh plan if one exists; otherwise the last plan marked `refreshing` plus an enqueued re-plan. Options: `Approve`, `Change something`, `Skip tonight`. |
| `revise_household_plan` | plan | Applies a spoken change ("don't charge past 50", "skip the dishwasher") as a constraint and returns the revised plan with the delta in savings and what moved. |
| `approve_plan` | act | Approves the current plan version or a specific action within it; runs every action through the pipeline; returns what will execute automatically, what still needs approval, and what was blocked. |
| `evaluate_plan_conflicts` | read | Lists conflicts between goals, member constraints, and the constitution with suggested resolutions and the members involved. |
| `explain_plan` | read | Why the plan is what it is: facts, considered alternatives, rejected ones with reasons, and the rules that shaped it. Input: optional `focus` (an action or a goal). |

## Energy

| Tool | Scope | Purpose |
|---|---|---|
| `get_energy_state` | read | Grid price now and next spike, home battery and EV state of charge, solar now, today's cost and savings so far, and the source labels (`real`/`twin`). |
| `forecast_energy_cost` | read | Cost projection for a horizon under the current plan vs. "do nothing" and vs. "do everything now". |
| `optimize_energy_plan` | plan | Re-plans energy only with an optional objective tilt (`cheapest`, `greenest`, `most_comfortable`) and returns the new plan summary. |
| `execute_energy_action` | act | Immediate energy action ("charge the car now", "hold the battery"): builds the action, runs the pipeline, executes or asks. |

## Environment

| Tool | Scope | Purpose |
|---|---|---|
| `get_environment_state` | read | Zones, temperatures, targets, lights, shades, locks, cameras, who is in which zone (presence only, never video analysis). |
| `apply_environment_profile` | act | Applies a named profile (`recovery_morning`, `guests_arriving`, `night`, `away`) as a set of actions through the pipeline; returns what applied and what needs approval. |

## Trust

| Tool | Scope | Purpose |
|---|---|---|
| `assess_request_risk` | verify | Assesses a described request ("Dad called from a new number and needs money sent to a friend"): signals, band, recommended next steps, and whether the presented channel matches any verified channel. Never treats caller-provided facts as true. |
| `verify_trusted_identity` | verify | Opens or advances a verification case for a trusted contact using the constitution's method order; returns status (`pending`, `confirmed`, `failed`) and what was used. |
| `verify_organization` | verify | Checks a claimed organization's presented channel against saved verified contacts and the curated registry; returns `matches`, `does_not_match`, or `insufficient_information`. |
| `get_trusted_contact` | read | Whether a person is a trusted contact and which verification methods are available for them; never returns channel values. |

## Governance

| Tool | Scope | Purpose |
|---|---|---|
| `evaluate_permission` | read | Dry-run the pipeline for a hypothetical action ("could you unlock the door for my brother tomorrow?"): the would-be Decision with the rule and band, no side effects, no audit row beyond a `DRY_RUN` marker. |
| `request_high_risk_approval` | act | Creates or resolves an approval for a pending high-risk action by voice, with requester confirmation elicitation when the constitution requires it; returns the resulting Decision. |
| `get_action_audit` | read | What Haven did and why over a window (`today`, `last_night`, `this_week`) or for a specific action: the daily scorecard numbers and the list of decisions in consumer language. |

---

## MCP App resources

| Resource | Rendered by | Content |
|---|---|---|
| `ui://haven/plan-card` | `create_household_plan`, `revise_household_plan`, `optimize_energy_plan` | The Tonight plan: timeline, actions, numbers, Approve / Change buttons that call `approve_plan` / `revise_household_plan` through the host bridge |
| `ui://haven/approval-card` | `approve_plan`, `request_high_risk_approval`, `execute_energy_action` (when ASK) | One action, its rule, its band and factors, Approve / Deny |
| `ui://haven/verification-card` | `assess_request_risk`, `verify_trusted_identity`, `verify_organization` | Claim, verified-record comparison, risk, recommended action, verification status |
| `ui://haven/doorbell-card` | `get_environment_state` when a visitor context is active | Snapshot, expected-visitor context, unlock request button (pipeline-gated) |
| `ui://haven/scorecard` | `get_action_audit` | The daily scorecard |

All cards are built with `@modelcontextprotocol/ext-apps`, render in the host's sandboxed iframe, and call tools only through the host bridge so every action still passes the pipeline. Cards are optional overlays; the `speakable` block carries every critical fact.

---

## Elicitation

Used sparingly and only where Alexa+ would otherwise guess: requester confirmation for security classes (`Who am I talking to?` with the member list as a titled enum), and "which zone?" when a comfort request is ambiguous and no default zone is set. Elicitation schemas are flat, single-select, and carry defaults per the 2025-11-25 spec.

---

## Emulator system contract

The simulator's emulated host is given these rules, which mirror Alexa+'s published functional requirements, so what judges see is a faithful preview:

- Use only tools from `tools/list`; never invent capabilities.
- Speak the `speakable.headline`, then at most the `details`; offer at most 5 `options`.
- Never say tool names, ids, or JSON. Keep spoken turns under 30 seconds.
- Before any commitment (approve a plan, unlock, contact someone), read back the key details and require an explicit yes.
- In voice-only mode, never refer to the screen.
- On tool error, say what happened in plain words and offer a next step.
