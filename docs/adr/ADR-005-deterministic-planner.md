# ADR-005 — Deterministic MILP planner; the LLM only narrates

**Status:** Accepted (2026-09-15)

**Decision:** Household plans are produced by a rolling-horizon mixed-integer linear program solved with HiGHS via `scipy.optimize.milp`, with a greedy heuristic for cold starts. Bedrock Claude turns the plan's structured facts into narration data. No model participates in choosing actions or times.

**Reasoning:**

- Energy scheduling under prices, deadlines, comfort bands, and member constraints is a textbook MILP. The solver gives an optimum, a gap, and a baseline to compute savings against, which makes the scorecard's numbers defensible.
- Explainability follows from structure: the binding constraints and the rejected alternatives are outputs of the model, not stories.
- Determinism keeps the planner off the model budget and off the Alexa latency path (it runs on triggers, never inside a tool call).
- One dependency (`scipy`) already common in the stack; HiGHS handles the instance sizes (about 800 variables) in well under a second.

**Alternatives considered:**

- *LLM planning with tool calls.* Fluent but unverifiable; would produce the 42 kW charger the original mockup accidentally implied. Rejected.
- *OR-Tools CP-SAT.* Excellent solver, larger dependency and a different modeling style; not needed at this scale. Revisit if appliance sequencing grows combinatorial.
- *EMHASS (the Home Assistant energy-management add-on).* It already optimizes solar, a battery, and deferrable loads including EV charging with a linear program, so "an energy optimizer" is not what Hirz adds. Not adopted as a component: its configuration model has no place for member constraints with provenance, per-occupant comfort bands, or a constitution's bounds, and wrapping it would be more code than the 800-variable model it would replace. It is the benchmark: the README's claim is governance over coordinated automation, not a better optimizer, and the backtest compares against a timer schedule and a cheapest-slots strategy rather than against doing nothing (added 2026-09-17).
- *Rule-based scheduling (charge in cheapest slots).* Kept as the heuristic fallback; rejected as the primary because it cannot trade comfort against cost or respect coupled constraints.

**Consequences:** Every physical parameter (charger kW, battery kWh, zone R and C) is a knob in the household graph and the scenario file because real hardware never matches the model on paper; the planner exposes `optimality_gap` and the executor's verify-after-act feeds deviations back as re-plan triggers.

## Scheduled action authority amendment — 2026-09-18 (author-approved)

**Decision:** A scheduled action carries `requested_by` of the member who approved
its plan, with `surface: scheduler`. A plan nobody approved does not execute.
An autonomous re-plan inherits the approving member of the plan it supersedes.
Scheduled actions never run as `unknown` or a synthetic system identity.
Households can tighten scheduled behaviour with `requester.surface == "scheduler"`
conditions, which the existing grammar already supports. Implementation belongs
to roadmap item 19.

**Reasoning:** Authority must trace to a person for the audit row and the boundary's
`requester_role` input; a plan approval is exactly that trace. Scheduling or
re-planning does not create a new source of authority, and execution-time pipeline
re-evaluation still applies.

**Rejected alternatives:**

- *Run as the household owner:* substitutes the owner's authority for the actual
  approver's and misattributes the action.
- *Run as a system role:* invents authority without a person and requires a new
  policy role outside the household's existing member rules.
- *Run as unknown and rely on auto rules:* loses the approval trace and is denied
  by the seeds' `per_role.unknown: '*': never`; auto rules cannot override that veto.
