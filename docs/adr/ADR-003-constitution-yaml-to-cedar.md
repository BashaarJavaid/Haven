# ADR-003 — YAML constitution, constrained grammar, compiled to Cedar, enforced twice

**Status:** Accepted (2026-09-15)

**Decision:** The household constitution is authored as YAML (via form, YAML, or plain English) with a small non-Turing-complete condition grammar, validated by a Pydantic schema and a tighten-only rule against the risk floors, and compiled to a Cedar/Dogwood policy set. It is enforced in-process by Haven's evaluator (pipeline stages 2, 4, 6) and again at the AWS tool boundary by AgentCore Policy (stage 7), with `cedarpy` standing in locally. Disagreement fails closed.

**Reasoning:**

- Households need a document they can read, diff, and roll back. YAML with a sentence rendered per rule satisfies that; Cedar alone does not (it is precise but not a household-facing format).
- The grammar is deliberately tiny so every rule is decidable, auditable, and safe to evaluate on every action without a sandbox. The missing-attribute rule (whole condition not satisfied before negation) is inherited from the author's ABAC evaluator, where the `not(...)` inversion bug was found and fixed.
- Cedar is the right target: default-deny, forbid-wins, schema validation against the tool definitions, automated analysis for always-allow and never-satisfiable policies, and temporal (Dogwood) rules that express "approval must precede action within the TTL" without custom code. AgentCore Policy evaluates it at the Gateway, outside Haven's process, which is a genuinely independent enforcement point.
- Two engines evaluating the same policy over the same facts is redundancy that fails closed. It catches bugs in Haven's pipeline and any path that would reach an adapter without a decision.

**Alternatives considered:**

- *Cedar as the authoring format.* Rejected for households; kept as the compiled and enforced form.
- *Natural language as the stored policy, interpreted by a model at decision time.* Rejected outright: non-deterministic, un-analyzable, and vulnerable to injection. Natural language is an authoring aid that produces a YAML patch a member activates.
- *OPA/Rego.* Capable, but no managed enforcement point in the AWS stack and no temporal support; Cedar's analysis and AgentCore integration won.
- *In-process evaluation only.* Simpler, but loses the independent boundary that makes "enforced at the AWS tool boundary" true rather than a slide.

**Consequences:** The class list, the risk table, the Cedar action names, and the Gateway target's tools must stay aligned; a test generates all four from `haven/risk/classes.yaml`. Temporal quotas (25 policies per engine, 3 operators per policy, 24 h window) are checked at compile time. Activating a new temporal policy set invalidates open policy sessions, so activation starts a new plan session.
