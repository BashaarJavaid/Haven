# The Household Constitution

The constitution is the document that answers "how much authority does Hirz have?" It is written by the household, versioned, validated, compiled to Cedar, and enforced twice: inside Hirz's decision pipeline and at the AWS tool boundary. This file is the spec. `ARCHITECTURE.md` §5.2 covers the engine; `THREAT_MODEL.md` covers what the constitution can and cannot guarantee.

---

## 1. Principles

1. **Three modes, no fourth.** Every action class, for every role, resolves to exactly one of `auto`, `ask`, `never`. There is no "auto but notify" mode; notification is a separate, always-on property of the audit trail.
2. **Tighten only.** A constitution can make Hirz more cautious than the risk floor, never less. `auto` on a CRITICAL class is rejected at validation, not silently ignored.
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
      never_for: [unexpected_visitor]
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

The schema above is the full shape. The demo seed `constitutions/quinn-home.yaml` starts at version 7 **without** `never_for: [unexpected_visitor]`, because that rule is proposed by voice and activated on camera as version 8 (`docs/demo-script.md`); `constitutions/quinn-parents.yaml` is the small second seed for Mom and Dad's home, with Malik as a trusted contact.

The closed list lives in `hirz/risk/classes.yaml` and is the same list the risk table uses. A constitution referencing an unknown class fails validation. Classes are namespaced `domain.class` and each carries its static risk profile (`ARCHITECTURE.md` §5.3). Adding a class is a code change with a test, because it also needs a risk profile, a Cedar action, and a tool mapping.

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

A household can also **pause** Hirz (`ARCHITECTURE.md` §5.14): while paused, every `auto` resolves as `ask`. Pause is a mode on the household, not a constitution version; it only tightens, so a voice may set it, and only the app clears it.

### 2.5 Identity on a shared device

Alexa delivers one access token per linked Amazon account and no speaker identity (`ARCHITECTURE.md` §7). A rule such as `per_role.teen.security.door_unlock: never` binds to the teen's *linked account*; it says nothing about who is standing in front of the kitchen Echo, where anyone speaks with the linked owner's authority. The constitution handles this with three rules, all enforced by the validator and the pipeline, not by trust in the speaker:

1. **Security is approved on a phone, never by voice.** A rule's `ask_channels` (defaulting to `defaults.ask_channels`) names where the approval may be given. For every class in the `security` domain, `ask_channels` must not contain `alexa`; the validator rejects a constitution that says otherwise. A spoken "yes" to a security question is therefore never an approval: Alexa reports that the request is waiting in the companion app, where approval is passkey-gated and attributable to one person. Non-security classes may keep `alexa` in their channels.
2. **The surface is a condition.** `requester.surface` (`alexa`, `app`, `scheduler`) is available to conditions and overrides, so a household can tighten any class on the shared surface, for example `hvac_adjust` with `- when: "requester.surface == 'alexa' and context.hour >= 22"` → `ask`. The pipeline sets the surface from the transport; it is never a request parameter.
3. **Claimed identity and any future speaker hint only lower authority.** `requester.claimed_role` (from the "Who am I talking to?" elicitation) and `requested_by.speaker` (null today; reserved for a recognized-speaker identifier if Alexa ever passes one) can match or reduce the linked account's role, never raise it.

---

## 3. Plain-English authoring

Sentences arrive two ways and end the same way, as a YAML diff a person activates on their own phone:

- **In the companion app**, typed or dictated on the Constitution page.
- **By voice through Alexa**, with the `propose_household_rule` tool (`docs/tool-catalog.md`). The tool call only records the sentence and writes a `CONSTITUTION_PROPOSED` audit row; no model runs inside the call. The worker drafts the patch, and the diff is pushed to the companion app. Alexa says the rule is waiting on the phone and will not take effect until it is approved there. A voice can propose; a voice can never activate. On a shared Echo anyone in the room can speak, so a spoken rule change, whether it tightens or loosens, is always only a proposal, and activation is passkey-gated and attributable to one person. This is principle 6 applied to the rules themselves.

Either way the drafting step produces a YAML diff, never a direct activation:

> "Never unlock the door for someone we're not expecting. Ask me before running the dishwasher after 10 at night. You can keep the house comfortable on your own as long as nobody is asleep in the room."

Bedrock Sonnet 5 receives the current YAML, the class list with descriptions, the grammar, and the sentences as delimited data, and must return a YAML patch plus one English sentence per changed rule. The patch is validated by the schema, compiled, analyzed (AWS mode), and shown as a diff with the sentences. The household activates it explicitly. The model never activates anything and never sees adapter credentials or member channels.

The diff screen shows, per changed rule, the English sentence, what changes in concrete situations, and a collapsed line with the compiled Cedar. The situation lines are **derived, never drafted**: a fixed list of situations per action class (`hirz/constitution/situations.yaml`) is evaluated against the current and the proposed version with the same evaluator `hirz decide` uses, and every situation whose outcome changed is shown as a before-and-after line ("Unexpected visitor: ask on phone → never"), next to the ones a household would expect to change and did not ("Expected arrival: still asks on your phone"), followed by the standing caveat of each class touched ("Hirz does not identify the visitor"). A drafting mistake therefore shows up as a line the household did not ask for.

**Sentences the grammar cannot say.** "Someone I don't know", "someone we aren't expecting", and "outside a scheduled arrival window" are three different rules, and Hirz can enforce only the last two, which are the same thing to it: a press that matches no expected arrival (`unexpected_visitor`). Hirz never identifies a person, so it has no notion of "know". When a sentence asks for something the grammar cannot express, the drafter must return the nearest rule it can express and say so in its sentence ("I can't tell who someone is. I can refuse anyone who isn't expected."), and the situation lines make the difference visible before activation.

`HIRZ_LLM=off` disables drafting and shows the form editor only. A scenario may carry a **recorded patch** for a sentence (`constitution.activate` with `patch:`), labeled as recorded, so headless runs and credential-less judges still exercise propose → diff → activate.

---

## 4. Compilation to Cedar

Every activated version compiles to one Cedar/Dogwood policy set. Naming: `AgentCore::Action::"HirzActions___<domain>_<class>"` (the Gateway target `HirzActions` exposes one tool per class), resource the Gateway. The principal is the worker's machine identity: a scheduled action comes due long after the member's token expired, so the worker calls the Gateway with its own token, and the requester's role and the household travel as input fields (`requester_role`, `household`) that Hirz supplies. Every `permit` and `forbid` is scoped to its household, because two constitutions on one engine would otherwise lend each other permits.

`auto` with conditions:

```cedar
permit (
  principal,
  action == AgentCore::Action::"HirzActions___energy_hvac_adjust",
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:123456789012:gateway/hirz"
)
when {
  context.input.household == "quinn-home" &&
  ["owner", "adult"].contains(context.input.requester_role) &&
  context.input.target_f >= 66 && context.input.target_f <= 76 &&
  context.input.zone_sleeping == false
};
```

`never`:

```cedar
forbid (
  principal,
  action == AgentCore::Action::"HirzActions___finance_transfer_money",
  resource
)
when { context.input.household == "quinn-home" };
```

`ask` (temporal: an approval response must precede the action within the TTL, bound to the same action hash). The temporal permit is **generic**: it does not name the action class. One is emitted per distinct `approval_ttl_minutes` value in the constitution (usually one or two), not one per `ask` class, so the engine's quota of 25 temporal policies is never approached:

```cedar
permit (
  principal,
  action,
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:123456789012:gateway/hirz"
)
when temporal {
  formerly within 30m AgentCore::Action::"HirzActions___governance_approve_action"::response {
    eventResource:            resource,
    input.household:          context.input.household,
    input.action_class:       context.input.action_class,
    input.action_hash:        context.input.action_hash,
    output.ttl_minutes:       30,
    output.approved:          true
  }
};
```

The snippet shows intent; the exact field-matching syntax, and whether five matched fields fit the engine's per-policy operator limit, is settled at the `ROADMAP.md` item 7 gate. If it does not fit, household and class move into the hash's preimage check in the Lambda, which already recomputes it.

Four properties this permit must have, each with a test (`ARCHITECTURE.md` §12):

1. **An approval for one class cannot authorize another.** The approval event and the action must name the same class, and the hash covers the class.
2. **A short approval cannot ride a longer permit.** Cedar permits are alternatives, so the thirty-minute permit would happily match an approval given under a ten-minute rule. Each temporal permit matches only approvals whose `ttl_minutes` equals its own, and the per-class stateless permit on `approve_action` pins the class to its TTL group.
3. **The hash is recomputed, never trusted.** `action_hash` arrives from the worker. The `hirz-actions` Lambda recomputes it from the class, target, params, and scheduled time on both calls (`approve_action` and the action) and refuses on a mismatch, so a worker bug cannot present an unlock under the hash of an approved lights action.
4. **One approval, one operation.** "Approved within thirty minutes" is not "approved once", and a temporal policy cannot count. Consumption is enforced where the action lands: Hirz Link refuses a `content_hash` it has already executed (`ARCHITECTURE.md` §5.17), and the in-process pipeline marks the approval redeemed.

What this permit does **not** establish is that a person approved. The `approve_action` call reaches the Gateway through the worker, so a fully compromised worker could claim an approval that never happened. `ROADMAP.md` item 38d closes that for `security.*` classes by verifying the member's passkey assertion, over the action hash, inside the Lambda ([ADR-010](./adr/ADR-010-passkey-verified-approvals.md)); until it is built, `THREAT_MODEL.md` says No.

*Who* may approve *what* is enforced on the stateless permit for `approve_action` itself: one `permit` per `ask` class on `HirzActions___governance_approve_action` with `context.input.action_class == "..."`, the rule's TTL group (`context.input.ttl_minutes == 30`), the rule's `allowed_requesters` as a condition on `requester_role`, and its quorum inputs. An approval that was not permitted is recorded as an `error` event, and the generic temporal permit matches only `response` events, so it can never be satisfied by a refused approval. `never` classes carry a `forbid`, which wins over the generic permit.

Compilation facts the engine relies on:

- Cedar is default-deny and forbid-wins, so `never` rules cannot be overridden by any `permit`, matching principle 2.
- **What the boundary is independent about.** The Gateway sees only the request: the action, the resource, and the input fields. Action class, parameter bounds (`target_f` within 66–76), the action hash (recomputed by the Lambda), and the order of approval and action are therefore evaluated independently of Hirz. The requester's role is not: it is an input Hirz supplies, like the context facts. Occupancy, sleeping, quiet-hours, and other context facts are not in the request; the Executor passes them as input fields (`zone_sleeping`, `is_quiet_hours`) computed from the same context snapshot the pipeline used, and the snapshot hash is included in the call so the audit row can prove both engines saw the same facts. The boundary catches a compiler bug, a pipeline bug, or a bypass path; it does not catch a wrong snapshot. `THREAT_MODEL.md` says the same.
- **A permit is what gets a command signed.** For devices in the home, the Gateway target does not call the device. On a permit, the `hirz-actions` Lambda signs the command with a KMS key only its role can use, and the home-side agent (Hirz Link) executes only commands whose signature verifies ([ADR-009](./adr/ADR-009-signed-commands-home-agent.md)). Hirz's own processes hold no credential that can act on a device, so a path that skips the boundary has nothing to act with. The command is addressed to one home (`home_id`), executed at most once, and for a bounded operation carries its own ending, which the home runs from its own clock (`ARCHITECTURE.md` §5.6).
- Temporal rules require the policy session header on every Gateway call; the Executor uses the plan session id. Quotas (25 temporal policies per engine, 3 operators per policy, 24-hour window) are still checked at compile time and fail activation with the count if exceeded.
- **One evaluator locally, and it is Dogwood's.** Every Cedar policy is a valid Dogwood policy, so the identical policy text is evaluated locally by the open-source Dogwood CLI (`validate`, `replay`, `lower`, `check-parse`) behind a thin subprocess wrapper, fed the compiled set plus the session's event trace. Hirz does not reimplement temporal semantics. `tests/cedar_conformance` asserts Dogwood and AgentCore Policy produce the same decision for every scenario action. Locally the evaluator runs in the same container as the pipeline, so it is a **second evaluator in the same trust domain**, not a boundary outside Hirz; the audit row's `boundary.engine` reads `dogwood-local` and the Cedar view says so. Only AWS mode has the out-of-process boundary. If the CLI turns out not to be drivable this way (`ROADMAP.md` item 7 verifies it early), the fallback is `cedarpy` for stateless rules plus an in-process record for the single generic temporal rule, and the docs are updated to say so.
- Changing temporal policies invalidates open policy sessions on the engine (HTTP 409 on reuse). Activation therefore starts a new plan session and re-issues pending approvals under it.

---

## 5. Lifecycle

```
[proposed by voice: sentence recorded, CONSTITUTION_PROPOSED]  →
draft (form | yaml | english)  →  validate (schema, class list, tighten-only, security-never-by-voice, grammar)
  →  compile (Cedar + Dogwood)  →  dogwood validate (syntax + schema; everywhere)
  →  [AWS mode] AgentCore Policy automated reasoning on create/update (no always-allow, no never-satisfiable)
  →  preview (diff + sentences + derived situation lines + analysis where available)  →  activate (journaled: write version, audit CONSTITUTION_ACTIVATED, swap)
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
| Malik asks to unlock the door for "the plumber" not on the schedule, under version 7 (no `never_for`) | `ask` → ASK on the phone | The household has not written a veto; a security class still asks, and never by voice |
| The same request after Malik activates version 8 with `never_for: [unexpected_visitor]` | DENY_CONSTITUTION, citing version 8 | The household wrote the veto; it holds regardless of the requester. Same lock, different outcome, because the family changed the rule |
| Someone rings at 19:04; Mom is expected at 19:00; Malik says "that's my mom, let her in" | `ask` → ASK (quorum any_adult, channel `app_push`): "Someone is at the front door. Mom is expected now." → Malik approves in the companion app → APPROVED → EXECUTE, relock at 10 min run by Hirz Link | Inside an expected window, so not an `unexpected_visitor`; the schedule is context and Malik's approval is the identification; `max_open_minutes` |
| A stranger rings at 19:04, inside Mom's window | Exactly the same ASK with the same sentence; Malik looks at the snapshot and denies → REJECTED | The schedule cannot tell Mom from a stranger and never claims to |
| Someone at the kitchen Echo answers "yes" to "Unlock the front door?" | Not an approval; Alexa says the request is waiting on Malik's phone | `security.*` excludes `alexa` from `ask_channels` (§2.5); a voice cannot be attributed to a person |
| A constitution lists `ask_channels: [alexa]` on `security.door_unlock` | Validation refused | Voice never approves security (principle 6) |
| Mom: "Malik called from a strange number and needs five hundred dollars. Is it really him?" | `finance.verify_request` `auto` → assessment lands CRITICAL → VERIFY; Malik answers in his own app | Hirz has no way to move money, by design, and no money action is offered to the orchestrator; a money request is assessed, not executed. `finance.transfer_money` stays `never` with a CRITICAL floor so the scam-pattern factor has a class to attach to |
| Today's autonomous energy actions have already spent $9.60 of the daily budget and the next battery dispatch would spend $0.80 | `ask` → ASK_BUDGET | budget `usd_per_day: 10` nearly consumed (the budget caps spend, not savings) |
| Constitution says `auto` for `access_code_share` | Activation refused | CRITICAL classes cannot be `auto` (tighten-only vs. the risk floor) |
