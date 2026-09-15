# ADR-004 — Table-driven risk bands, no formula, no model

**Status:** Accepted (2026-09-15)

**Decision:** Risk is a static per-class profile (impact, reversibility, base band) plus a fixed list of dynamic factors that can only raise the band. No numeric formula such as Impact × Uncertainty × Irreversibility, no learned model, no LLM.

**Reasoning:**

- A household must be able to read why an action was asked about or refused. "Door unlock is HIGH; a guest is present, so it's CRITICAL" is a sentence. A product of three estimated numbers is not, and nobody can defend the numbers.
- Bands map directly onto the constitution's three modes and to floors the constitution can tighten but not loosen. That is the property that makes "safe autonomous action" a system guarantee.
- Deterministic scoring is testable exhaustively and cannot be steered by injected text.
- The original concept's formula was useful as a mental model; as code it would be false precision.

**Alternatives considered:**

- *Weighted numeric score with thresholds* (as in the author's gateway). Works there for a security operator audience; rejected here because the audience is a family and the classes are few enough to enumerate.
- *LLM-assessed risk.* Rejected: non-deterministic, injectable, unexplainable. The one place a model touches risk is Protect's signal *extraction*, which is schema-validated and then weighted by code.
- *Learned per-household risk.* Rejected for v1; the consent-gated memory path can later propose per-household tightening, never loosening.

**Consequences:** Adding an action class is a code change with a risk profile, a Cedar action, a tool mapping, and a test. Bands are compared in exactly one function.
