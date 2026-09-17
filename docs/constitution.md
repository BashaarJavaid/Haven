# The Household Constitution

The constitution is the document that answers "how much authority does Haven have?" It is written by the household, versioned, validated, compiled to Cedar, and enforced twice: inside Haven's decision pipeline and at the AWS tool boundary. This file is the spec. `ARCHITECTURE.md` §5.2 covers the engine; `THREAT_MODEL.md` covers what the constitution can and cannot guarantee.

---

## 1. Principles

1. **Three modes, no fourth.** Every action class, for every role, resolves to exactly one of `auto`, `ask`, `never`. There is no "auto but notify" mode; notification is a separate, always-on property of the audit trail.
2. **Tighten only.** A constitution can make Haven more cautious than the risk floor, never less. `auto` on a CRITICAL class is rejected at validation, not silently ignored.
3. **Explicit beats implicit.** An action class with no rule resolves to `ask` for adults and `never` for everyone else. Silence is not consent.
4. **Readable by the household.** Every rule round-trips to a plain-English sentence the companion app shows next to it. If the engine can't render a rule as a sentence, the rule is invalid.
5. **Analyzable.** The compiled Cedar set is validated against the tool schema everywhere. In AWS mode it is also analyzed by AgentCore Policy's automated reasoning on create or update; a policy that always permits, or a condition that can never be satisfied, fails activation with an explanation. No local library performs that analysis, so local activation runs the structural checks only and says so.
6. **Voice never approves security.** An Echo is a shared device and Alexa does not tell add-ons who spoke, so a role cannot be enforced by voice. Every `security.*` rule in `ask` mode must route its approval to a per-person channel (`app_push`, passkey-gated); a constitution that lists `alexa` as an ask channel for a security class fails validation. See §2.5.

---

## 2. Schema (YAML)

```yaml
version: 7                      # monotonic; assigned on activation
household: quinn-home
defaults:
  unlisted_class: ask           # for adults; other roles fall to never
  approval_ttl_minutes: 30
  ask_channels: [alexa, app_push]

roles:                           # who can hold which role is in the household graph, not here
  owner: {inherits: adult}
  adult: {}
  caregiver: {inherits: adult, limited_to: [environment, health, communication]}
  teen: {}
  child: {}
  guest: {}
  unknown: {}                    # unresolvable requester

autonomy:
  energy:
    optimize_cost:
      mode: auto
      budget: {usd_per_day: 10}
      bounds: {ev_soc_floor: 0.30}
    ev_charge:
      mode: auto
      conditions:
        - "asset.policy.needed_by is set"
    battery_dispatch:
      mode: auto
    hvac_adjust:
      mode: auto
      bounds: {min_f: 66, max_f: 76}
      conditions:
        - "not occupancy.sleeping_in(action.target.zone)"
      overrides:
        - when: "occupancy.sleeping_in(action.target.zone)"
          mode: ask
    appliance_start:
      mode: auto
      conditions:
        - "context.hour >= 7 and context.hour < 22"
      overrides:
        - when: "context.hour >= 22 or context.hour < 7"
          mode: ask
  environment:
    lights:
      mode: auto
    comfort_profile:
      mode: auto
    shades:
      mode: auto
  security:
    door_unlock:
      mode: ask
      quorum: any_adult
      ask_channels: [app_push]       # security is never approved by voice (§2.5)
      allowed_requesters: [owner, adult]
      never_for: [unknown_visitor]
      max_open_minutes: 10
    camera_disable:
      mode: ask
      quorum: owner
      ask_channels: [app_push]
      max_minutes: 120
    access_code_share:
      mode: never
    arm_disarm:
      mode: ask
      ask_channels: [app_push]
  finance:
    transfer_money:
      mode: never
    change_payee:
      mode: never
    verify_request:
      mode: auto
  health:
    comfort_preferences:
      mode: auto
    routine_reminders:
      mode: auto
    medical_decisions:
      mode: never
  communication:
    notify_member:
      mode: auto
    contact_trusted_contact:
      mode: auto
    contact_emergency_services:
      mode: ask
      quorum: any_adult

per_role:                        # role-specific tightening; can only tighten
  teen:
    security.door_unlock: {mode: never}
    energy.hvac_adjust: {mode: ask}
  child:
    "*": {mode: never}
  guest:
    environment.lights: {mode: auto}
    "*": {mode: never}
  unknown:
    "*": {mode: never}

quiet_hours:
  - {days: [mon, tue, wed, thu, sun], from: "22:30", to: "06:30", affects: [appliance_start, lights]}

verification:
  require_requester_confirmation: [security.door_unlock, security.camera_disable]
  trusted_contact_methods_order: [app_confirmation, verified_callback, safe_word, verified_email]

learning:
  accept_memory_proposals: manual   # manual | never
```

### 2.1 Action classes

The closed list lives in `haven/risk/classes.yaml` and is the same list the risk table uses. A constitution referencing an unknown class fails validation. Classes are namespaced `domain.class` and each carries its static risk profile (`ARCHITECTURE.md` §5.3). Adding a class is a code change with a test, because it also needs a risk profile, a Cedar action, and a tool mapping.

### 2.2 Modes and precedence within a rule

For a given class and requester:

1. `per_role[role][class]` if present, else `per_role[role]["*"]` if present.
2. Otherwise `autonomy[domain][class]` with its `overrides` evaluated top to bottom; the first `when` that is satisfied wins; otherwise the base `mode`.
3. Otherwise `defaults.unlisted_class` for `adult`-derived roles, `never` for everyone else.

A `per_role` entry may only tighten (`auto → ask → never`); a `per_role` that would loosen fails validation. The same rule applies to `overrides`: an override's `mode` must be at least as restrictive as the rule's base `mode`, so `mode: ask` with an override to `auto` fails validation. Overrides exist to ask or refuse in specific situations, never to grant.

### 2.3 Conditions grammar

```
condition  := expr
expr       := term (("and" | "or") term)*
term       := "not" term | comparison | predicate | "(" expr ")"
comparison := attr op literal | attr "in" "[" literal ("," literal)* "]"
predicate  := attr "is set" | attr "is not set" | fn "(" args ")"
attr       := ident ("." ident)*
op         := "==" | "!=" | "<" | "<=" | ">" | ">="
fn         := "occupancy.sleeping_in" | "occupancy.present" | "schedule.expected_within"
literal    := number | string | boolean | time
```

Available attribute roots: `context` (hour, weekday, is_quiet_hours, price_band), `occupancy` (present members, sleeping_any, sleeping_in(zone)), `action` (class, target, params), `requester` (role, member_id, claimed_role, surface), `asset` (the target asset's policy and state), `risk` (band, factors), `household` (budget_used_today).

Semantics: deterministic, side-effect-free, evaluated against one immutable context snapshot. Any reference to an attribute absent from the snapshot makes the *entire* condition not-satisfied before any `not`/`and`/`or` runs, and emits a `POLICY_ERROR` audit row naming the attribute. This is the same rule the author's PortunusMCP ABAC evaluator uses and for the same reason: a naive `False` at the leaf inverts under `not`.

Not in the grammar, on purpose: loops, recursion, user functions, string manipulation, arithmetic beyond literal comparison, and any way to reference another rule.

### 2.4 Budgets and bounds

`budget` is a hard daily cap enforced at pipeline stage 6 from `household.budget_used_today` (computed from the audit ledger). Reaching the cap turns `auto` into `ask` for the rest of the day; exceeding it by an in-flight action is `DENY_BUDGET`. `bounds` are numeric guards the risk engine also reads (`outside_bounds` factor). Physical safety clamps (`ARCHITECTURE.md` §10) are code and sit above any bound the constitution sets.

### 2.5 Identity on a shared device

Alexa delivers one access token per linked Amazon account and no speaker identity (`ARCHITECTURE.md` §7). A rule such as `per_role.teen.security.door_unlock: never` binds to the teen's *linked account*; it says nothing about who is standing in front of the kitchen Echo, where anyone speaks with the linked owner's authority. The constitution handles this with three rules, all enforced by the validator and the pipeline, not by trust in the speaker:

1. **Security is approved on a phone, never by voice.** A rule's `ask_channels` (defaulting to `defaults.ask_channels`) names where the approval may be given. For every class in the `security` domain, `ask_channels` must not contain `alexa`; the validator rejects a constitution that says otherwise. A spoken "yes" to a security question is therefore never an approval: Alexa reports that the request is waiting in the companion app, where approval is passkey-gated and attributable to one person. Non-security classes may keep `alexa` in their channels.
2. **The surface is a condition.** `requester.surface` (`alexa`, `app`, `scheduler`) is available to conditions and overrides, so a household can tighten any class on the shared surface, for example `hvac_adjust` with `- when: "requester.surface == 'alexa' and context.hour >= 22"` → `ask`. The pipeline sets the surface from the transport; it is never a request parameter.
3. **Claimed identity and any future speaker hint only lower authority.** `requester.claimed_role` (from the "Who am I talking to?" elicitation) and `requested_by.speaker` (null today; reserved for a recognized-speaker identifier if Alexa ever passes one) can match or reduce the linked account's role, never raise it.

---

## 3. Plain-English authoring

The companion app accepts sentences and produces a YAML diff, never a direct activation:

> "Never unlock the door for someone I don't know. Ask me before running the dishwasher after 10 at night. You can keep the house comfortable on your own as long as nobody is asleep in the room."

Bedrock Sonnet 5 receives the current YAML, the class list with descriptions, the grammar, and the sentences as delimited data, and must return a YAML patch plus one English sentence per changed rule. The patch is validated by the schema, compiled, analyzed (AWS mode), and shown as a diff with the sentences. The household activates it explicitly. The model never activates anything and never sees adapter credentials or member channels.

`HAVEN_LLM=off` disables this path and shows the form editor only.

---

## 4. Compilation to Cedar

Every activated version compiles to one Cedar/Dogwood policy set. Naming: `AgentCore::Action::"HavenActions___<domain>_<class>"` (the Gateway target `HavenActions` exposes one tool per class), principal `AgentCore::OAuthUser` with a `role` tag from the token, resource the Gateway.

`auto` with conditions:

```cedar
permit (
  principal,
  action == AgentCore::Action::"HavenActions___energy_hvac_adjust",
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:123456789012:gateway/haven"
)
when {
  principal.hasTag("role") && ["owner", "adult"].contains(principal.getTag("role")) &&
  context.input.target_f >= 66 && context.input.target_f <= 76 &&
  context.input.zone_sleeping == false
};
```

`never`:

```cedar
forbid (
  principal,
  action == AgentCore::Action::"HavenActions___finance_transfer_money",
  resource
);
```

`ask` (temporal: an approval response must precede the action within the TTL, bound to the same action hash). The temporal permit is **generic**: it does not name the action class. One is emitted per distinct `approval_ttl_minutes` value in the constitution (usually one or two), not one per `ask` class, so the engine's quota of 25 temporal policies is never approached:

```cedar
permit (
  principal,
  action,
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:123456789012:gateway/haven"
)
when temporal {
  formerly within 30m AgentCore::Action::"HavenActions___governance_approve_action"::response {
    eventResource:            resource,
    input.action_hash:        context.input.action_hash,
    output.approved:          true
  }
};
```

*Who* may approve *what* is enforced on the stateless permit for `approve_action` itself: one `permit` per `ask` class on `HavenActions___governance_approve_action` with `context.input.action_class == "..."`, the rule's `allowed_requesters` as a role-tag condition, and its quorum inputs. An approval that was not permitted is recorded as an `error` event, and the generic temporal permit matches only `response` events, so it can never be satisfied by a refused approval. `never` classes carry a `forbid`, which wins over the generic permit.

Compilation facts the engine relies on:

- Cedar is default-deny and forbid-wins, so `never` rules cannot be overridden by any `permit`, matching principle 2.
- **What the boundary is independent about.** The Gateway sees only the request: the principal's role tag, the action, the resource, and the input fields. Action class, requester role, parameter bounds (`target_f` within 66–76), the action hash, and the approval history are therefore evaluated fully independently of Haven. Occupancy, sleeping, quiet-hours, and other context facts are not in the request; the Executor passes them as input fields (`zone_sleeping`, `is_quiet_hours`) computed from the same context snapshot the pipeline used, and the snapshot hash is included in the call so the audit row can prove both engines saw the same facts. The boundary catches a compiler bug, a pipeline bug, or a bypass path; it does not catch a wrong snapshot. `THREAT_MODEL.md` says the same.
- Temporal rules require the policy session header on every Gateway call; the Executor uses the plan session id. Quotas (25 temporal policies per engine, 3 operators per policy, 24-hour window) are still checked at compile time and fail activation with the count if exceeded.
- **One evaluator locally, and it is Dogwood's.** Every Cedar policy is a valid Dogwood policy, so the identical policy text is evaluated locally by the open-source Dogwood CLI (`validate`, `replay`, `lower`, `check-parse`) behind a thin subprocess wrapper, fed the compiled set plus the session's event trace. Haven does not reimplement temporal semantics. `tests/cedar_conformance` asserts Dogwood and AgentCore Policy produce the same decision for every scenario action. If the CLI turns out not to be drivable this way (`ROADMAP.md` item 7 verifies it early), the fallback is `cedarpy` for stateless rules plus an in-process record for the single generic temporal rule, and the docs are updated to say so.
- Changing temporal policies invalidates open policy sessions on the engine (HTTP 409 on reuse). Activation therefore starts a new plan session and re-issues pending approvals under it.

---

## 5. Lifecycle

```
draft (form | yaml | english)  →  validate (schema, class list, tighten-only, security-never-by-voice, grammar)
  →  compile (Cedar + Dogwood)  →  dogwood validate (syntax + schema; everywhere)
  →  [AWS mode] AgentCore Policy automated reasoning on create/update (no always-allow, no never-satisfiable)
  →  preview (diff + sentences + analysis where available)  →  activate (journaled: write version, audit CONSTITUTION_ACTIVATED, swap)
  →  rollback (same path to a prior version)
```

Activation is refused while any `ask` for a class whose rule is changing has a pending approval; the UI lists them. Every version keeps its YAML, compiled Cedar, hash, and analysis report (or a recorded "not analyzed: local mode") so an auditor can re-derive the enforcement that applied to any past action.

---

## 6. Worked examples

| Situation | Resolution | Why |
|---|---|---|
| Malik (owner) asks to pre-warm the living room to 72 at 17:35; nobody asleep | `auto` → EXECUTE | `energy.hvac_adjust` auto, bounds met, condition met, band LOW |
| Same, at 23:40, Mom asleep in the guest room adjacent zone | `ask` → ASK | override `when occupancy.sleeping_in(zone)` → ask; risk factor `occupant_asleep` also raises to HIGH → ASK |
| Teen asks Alexa to unlock the front door | `never` → DENY_CONSTITUTION | `per_role.teen.security.door_unlock: never` |
| Malik asks to unlock the door for "the plumber" not on the schedule | `ask` + `never_for: unknown_visitor` → DENY_CONSTITUTION | Unknown visitor is a hard veto regardless of the requester |
| Malik asks to unlock for Mom, who is expected at 19:00 and rang at 19:04 | `ask` → ASK (quorum any_adult, channel `app_push`) → Malik approves in the companion app → APPROVED → EXECUTE, auto-relock at 10 min | Expected visitor; approval within TTL on a per-person channel; `max_open_minutes` |
| Someone at the kitchen Echo answers "yes" to "Unlock the front door for Mom?" | Not an approval; Alexa says the request is waiting on Malik's phone | `security.*` excludes `alexa` from `ask_channels` (§2.5); a voice cannot be attributed to a person |
| A constitution lists `ask_channels: [alexa]` on `security.door_unlock` | Validation refused | Voice never approves security (principle 6) |
| "Send $500 to Dad's friend" | `never` → DENY_CONSTITUTION, Protect opens a VerificationCase | CRITICAL floor and `never`; the verify path is `auto` |
| Today's autonomous energy actions have already spent $9.60 of the daily budget and the next battery dispatch would spend $0.80 | `ask` → ASK_BUDGET | budget `usd_per_day: 10` nearly consumed (the budget caps spend, not savings) |
| Constitution says `auto` for `access_code_share` | Activation refused | CRITICAL classes cannot be `auto` (tighten-only vs. the risk floor) |
