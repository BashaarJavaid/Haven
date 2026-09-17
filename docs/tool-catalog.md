# MCP Tool Catalog

The tool surface Alexa+ (and the simulator) sees. Five groups, eleven tools. The surface is deliberately small: an orchestrator picks reliably among eleven distinct verbs and unreliably among two dozen near-duplicates, and Alexa's own guidance is tools whose outputs feed each other. Every tool follows the same contract:

- **Input** is a JSON Schema 2020-12 `inputSchema` with every parameter described in consumer terms and with synonyms (Alexa+ resolves "the living room", "lounge", "front room" through the description).
- **Output** conforms to an `outputSchema` and always includes `speakable` (`headline`, `details[≤3]`, `options[≤5]`) so voice-only devices are complete, plus structured `data`, plus optional `ui` (an MCP App resource reference) for display devices.
- **Errors** are MCP tool-execution errors with a consumer-language `message` and a machine `code`; never protocol errors for validation problems, so the host can self-correct.
- **No internal IDs in speakable text.** Plan, action, and case ids travel in `data` and in `_meta` only.
- **Latency** under the §8 budget; nothing in a tool waits on a model, a solver, the Gateway, an adapter, or a third-party network call. Tools that act hand execution to the worker and say so in `speakable`.
- **Scopes** (OAuth): `haven:read`, `haven:plan`, `haven:act`, `haven:verify`. A token without the scope gets a friendly refusal, not a 401.

Naming follows the 2025-11-25 guidance: lowercase, underscores, verb first.

---

## Context

| Tool | Scope | Purpose |
|---|---|---|
| `what_can_you_do` | none | Returns a contextual capability summary ("Tonight I can plan energy, keep the house comfortable for your parents, and check suspicious requests"). Required by Alexa+'s onboarding rules; works for unlinked users with a generic summary. |
| `get_household_context` | read | The household right now, by `scope`: `people` (who is home and expected), `member` (one member's preferences, role, presence, and whether they are a trusted contact and which verification methods are available; input `member` by name or relationship with synonyms; never returns channel values), `energy` (grid price now and next spike, battery and EV state of charge, solar, today's cost and savings so far, source labels), `environment` (zones, temperatures, targets, lights, shades, locks, cameras, presence per zone, any active doorbell visitor context), `constraints` (active constraints with provenance: "Dad: kitchen in use until 11 PM"), `plan` (current plan headline and approval state), `security` (unusual situations), or `all`. One read tool, one materialized view, one query. |

## Planning

| Tool | Scope | Purpose |
|---|---|---|
| `get_household_plan` | plan | The current plan for a horizon (`tonight`, `overnight`, `tomorrow_morning`, `next_24h`) with goals honored, actions, numbers, alternatives, and approval state. Optional `objective` tilt (`cheapest`, `greenest`, `most_comfortable`) requests a re-plan with that weighting. The summary always includes the "do nothing" and "do everything now" comparisons, so no separate forecast tool exists. Fresh plan if one exists; otherwise the last plan marked `refreshing` plus an enqueued re-plan. Options: `Approve`, `Change something`, `Skip tonight`. |
| `revise_household_plan` | plan | Records a spoken preference or constraint (`text`, `applies_to` member/asset/zone, optional `window`, `kind` ∈ `preference`, `constraint`, `one_time`) with the speaker as its provenance, runs Coordinator normalization, re-plans if it affects the plan, and returns the revised plan with the delta in savings and what moved. "Don't charge past 50" and "Dad's in the kitchen until eleven" both land here. |
| `explain_plan` | read | Why the plan is what it is: facts, considered alternatives, rejected ones with reasons, the rules that shaped it, and, with `focus: conflicts`, the conflicts between goals, member constraints, and the constitution with suggested resolutions and the members involved. Optional `focus` may also name an action or a goal. |

## Action

| Tool | Scope | Purpose |
|---|---|---|
| `approve_action` | act | Approves or declines the current plan, a specific action within it, or a pending approval, with requester confirmation elicitation when the constitution requires it. Runs pipeline stages 1–6 for what it approves; returns what is now executing (asynchronously, via the worker, `ARCHITECTURE.md` §5.6), what still needs approval, and what was blocked. Voice can resolve an approval only for classes whose `ask_channels` include `alexa`; for `security.*` classes (never voice-approvable, `docs/constitution.md` §2.5) the tool creates the approval, sends it to the companion app, and its `speakable` says the request is waiting on the phone. |
| `execute_household_action` | act | An immediate action: either a `class` with `params` ("charge the car now", "hold the battery", "turn on the living-room lamp") or a named `profile` (`recovery_morning`, `guests_arriving`, `night`, `away`) expanded to its set of actions. Runs pipeline stages 1–6 and either asks or hands each action to the worker for execution within seconds. Returns the Decision(s) with `status: executing` and a `speakable` such as "Starting the charge now"; the verified outcome lands in the audit ledger and is reported by `get_action_audit`, the plan card, and a push notification. The call never waits on the Gateway or an adapter. |

## Trust

| Tool | Scope | Purpose |
|---|---|---|
| `assess_request_risk` | verify | Assesses a described request against the household's own records. `claimed_party: person` ("Dad called from a new number and needs money sent to a friend"): signals, band, recommended next steps, and whether the presented channel matches any of that person's verified channels. `claimed_party: organization` ("someone from the utility is asking for a payment"): checks the presented channel against saved verified contacts for that organization and the curated registry and returns `matches`, `does_not_match`, or `insufficient_information`. Never treats caller-provided facts as true. |
| `verify_trusted_identity` | verify | Opens or advances a verification case for a trusted contact using the constitution's method order; returns status (`pending`, `confirmed`, `failed`) and what was used. Asked about someone with no open case, it reports whether they are a trusted contact and which verification methods are available; it never returns channel values. |

## Governance

| Tool | Scope | Purpose |
|---|---|---|
| `evaluate_permission` | read | Dry-run the pipeline for a hypothetical action ("could you unlock the door for my brother tomorrow?"): the would-be Decision with the rule and band, no side effects, no audit row beyond a `DRY_RUN` marker. |
| `get_action_audit` | read | What Haven did and why over a window (`today`, `last_night`, `this_week`) or for a specific action: the daily scorecard numbers (peak kWh avoided first) and the list of decisions in consumer language. |

### What was merged, and where it went

Earlier drafts listed twenty-three tools. Nothing was dropped; each capability now lives in one place: `get_household_member`, `get_current_constraints`, `get_energy_state`, and `get_environment_state` are scopes of `get_household_context`; `create_household_plan`, `optimize_energy_plan`, and `forecast_energy_cost` are `get_household_plan`; `record_household_preference` is `revise_household_plan`; `evaluate_plan_conflicts` is `explain_plan` with `focus: conflicts`; `approve_plan` and `request_high_risk_approval` are `approve_action`; `execute_energy_action` and `apply_environment_profile` are `execute_household_action`; `verify_organization` is `assess_request_risk` with `claimed_party: organization`; `get_trusted_contact` is answered by `verify_trusted_identity`.

---

## MCP App resources

| Resource | Rendered by | Content |
|---|---|---|
| `ui://haven/plan-card` | `get_household_plan`, `revise_household_plan` | The Tonight plan: timeline, actions, numbers, Approve / Change buttons that call `approve_action` / `revise_household_plan` through the host bridge |
| `ui://haven/approval-card` | `approve_action`, `execute_household_action` (when ASK) | One action, its rule, its band and factors, Approve / Deny (for `security.*` classes the card says the approval is on the phone and shows no Approve button) |
| `ui://haven/verification-card` | `assess_request_risk`, `verify_trusted_identity` | Claim, verified-record comparison, risk, recommended action, verification status |
| `ui://haven/doorbell-card` | `get_household_context` (scope `environment` or `security`) when a visitor context is active | Snapshot, expected-visitor context, unlock request button (pipeline-gated) |
| `ui://haven/scorecard` | `get_action_audit` | The daily scorecard |

All cards are built with `@modelcontextprotocol/ext-apps`, render in the host's sandboxed iframe, and call tools only through the host bridge so every action still passes the pipeline. Cards are optional overlays; the `speakable` block carries every critical fact.

---

## Elicitation

Used sparingly and only where Alexa+ would otherwise guess: requester confirmation for security classes (`Who am I talking to?` with the member list as a titled enum), and "which zone?" when a comfort request is ambiguous and no default zone is set. Elicitation schemas are flat, single-select, and carry defaults per the 2025-11-25 spec. The requester answer is recorded as *claimed* and can only lower the linked account's authority; it is never treated as identification (`ARCHITECTURE.md` §7).

---

## Emulator system contract

The simulator's emulated host is given these rules, which mirror Alexa+'s published functional requirements, so what judges see is a faithful preview:

- Use only tools from `tools/list`; never invent capabilities.
- Speak the `speakable.headline`, then at most the `details`; offer at most 5 `options`.
- Never say tool names, ids, or JSON. Keep spoken turns under 30 seconds.
- Before any commitment (approve a plan, unlock, contact someone), read back the key details and require an explicit yes.
- In voice-only mode, never refer to the screen.
- On tool error, say what happened in plain words and offer a next step.
