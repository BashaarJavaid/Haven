# Threat Model

What Haven protects against, what it explicitly does not, and the assumptions the design rests on. See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for how each protection is implemented and [`docs/adr/`](./docs/adr/) for why alternatives were rejected.

An explicit scope boundary is worth more to a technical reviewer than an implied claim of total coverage. **Rule for this file:** a row moves to "Yes" only when the code that earns it exists and its `verify:` check in `ROADMAP.md` passes. Claims never outrun the implementation.

---

## Threats

| Threat | Protected? | Notes |
|---|---|---|
| Haven takes an action the household marked `never` | **Yes** (planned, Phase 1) | Constitution `never` is pipeline stage 2, terminal, and compiles to a Cedar `forbid`, which wins over any permit. Two independent engines must agree before execution |
| Haven takes a high-risk action without asking | **Yes** (planned, Phase 1) | Risk floors are code: HIGH → ASK minimum, CRITICAL → never autonomous. A constitution cannot loosen a floor; over-broad `auto` fails activation |
| Approval reused for a different action (TOCTOU) | **Yes** (planned, Phase 3) | Approvals bind to the action `content_hash`; redemption re-runs the pipeline against current state; mismatch → `DENY_APPROVAL_MISMATCH`; expiry → `DENY_APPROVAL_EXPIRED` |
| Approval granted under conditions that no longer hold (someone fell asleep, a guest arrived) | **Yes** (planned, Phase 3) | Execution-time re-evaluation; a changed context turns execute into ask and revises the plan |
| Prompt injection through utterances, calendar titles, contact names, or scenario text | **Partial** | Model output never decides anything: the pipeline, risk engine, constitution, and executor are code. Injected text can at most distort an explanation or a Protect signal extraction, both of which are schema-validated and, for Protect, weighted by code. What Haven cannot control is Alexa+'s own orchestrator being manipulated into calling the wrong tool with the wrong arguments; the pipeline then treats that call like any other request from that member |
| Family-impersonation and organization-impersonation scams relayed by a member | **Partial** | Haven verifies against stored verified channels and the subject's own app, never against caller-supplied facts, and never moves money (no payment adapter exists). Haven cannot see the phone call itself and depends on the member relaying it; a member who acts without asking Haven is outside its reach |
| Unlock for an unknown visitor | **Yes** (planned, Phase 6) | `never_for: [unknown_visitor]` is a hard veto; expected-visitor context comes from the schedule and the household graph, never from video identification |
| Cross-household data access with a valid token | **Yes** (planned, Phase 4) | Every query is scoped by the `household_id` derived from the token; a two-household isolation test runs in CI |
| Stolen or leaked access token | **Partial** | Short-lived JWTs, `aud`-bound, refresh handled by the AS; the holder still gets the linked member's authority until expiry. Requester confirmation on security classes limits what a stolen adult token can do, but a claimed role only lowers authority. Revocation is the AS's job |
| Forged Ring doorbell event | **Yes** (planned, Phase 6) | HMAC-SHA256 signature verification with a replay window; unsigned or replayed events are dropped and audited |
| Tampered audit trail | **Yes** (planned, Phase 3) | SHA-256 hash chain plus per-row ECDSA signatures; independent verifier; exports are self-contained and verifiable |
| Silent divergence between what the household approved and what was enforced | **Yes** (planned, Phase 7) | Boundary agreement (stage 7) records both engines' decisions; disagreement fails closed and is audited; the conformance suite runs both engines over the corpus |
| Constitution authoring mistakes (always-allow, never-satisfiable, over-broad) | **Partial** | Cedar analysis rejects always-allow and never-satisfiable policies; tighten-only and risk floors reject dangerous `auto`. Analysis cannot know the household's intent; a rule that is valid and permissive is the household's decision |
| Physical harm from an unsafe setpoint or an open lock | **Partial** | Code-level clamps (HVAC range, maximum unlock and camera-off windows) apply regardless of policy. Haven does not control life-safety systems and must not be connected to them |
| A twin that lies about the world (stale or wrong observations) | **Partial** | Observations carry freshness; stale state raises the risk band; verify-after-act compares expected and observed. A twin is not a sensor; real deployments should use real adapters for anything safety-relevant |
| Unauthorized "learning" of preferences from conversations | **Yes** (planned, Phase 3) | Memory proposals are consent-gated; nothing learned is acted on until a member accepts it in the companion app |
| Model provider outage | **Yes** | Decisions never depend on the model; explanations and drafting degrade to templates and forms |
| Compromised Haven host or AWS account | **No** | The signing key, the database, and the credential vault are then lost; this is infrastructure hardening, not application logic |
| Malicious linked adult | **No** | Attributable after the fact through the audit trail; not prevented. Quorum rules limit what one adult can approve alone for classes that require `all_adults` |
| Face or voice identification of people | **No, by design** | Haven never identifies people from video or audio and never claims to. Requester identity is the linked account plus a *claimed* role; visitor identity is schedule context |
| Autonomous financial transfers | **No, by design** | No payment adapter exists or is planned; the classes exist only so the constitution can forbid them provably |

---

## Assumptions

- The household's authorization server (Cognito in AWS, the dev issuer locally) is correctly configured with PKCE S256, short token lifetimes, and a resource indicator bound to Haven. Haven does not defend against a misconfigured or compromised authorization server.
- Alexa+ delivers the linked account's access token faithfully and does not expose voice-identity claims to add-ons; Haven's identity model assumes only what the token proves.
- Home Assistant, Smartcar, Ring, ComEd, and Open-Meteo report state faithfully; Haven defends against stale and missing data, not against a lying upstream.
- The Postgres instance and the audit signing key are managed by the operator; Haven defends against external tampering with stored rows (hash chain, signatures), not against a database superuser.
- AgentCore Policy evaluates the compiled Cedar faithfully; the local `cedarpy` evaluator is a conformance check on Haven's compiler, not a second opinion on AWS.
- The digital twin is labeled as such in every surface, and no safety-relevant decision in a real home relies on twin data.
- Haven is not a medical device, not a life-safety system, and not a financial institution. It executes comfort preferences, energy schedules, and household coordination within a written boundary, and it verifies identity from records the household established in advance.
