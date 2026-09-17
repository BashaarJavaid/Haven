# Friction Log

Every friction point hit while building Haven against a third-party tool, API, SDK, doc, or CLI. Devpost awards up to a 10 percent judging bonus for these, applied at Stage One, so this is the cheapest score in the project. Entries are facts from a session: the doc URL, the exact error text, the date. Nothing invented, nothing padded. A short log of real entries beats a long one.

**Rule:** log at the moment friction happens, not at the end of the session. Trigger: a tool did not do what its docs said, cost more than about 15 minutes, or forced a workaround. Fields are the ones Devpost requires. Severity: `Blocker` (could not proceed without a workaround), `Major` (lost more than an hour or changed the design), `Minor` (annoyance, documented anyway).

Candidates are things expected to bite that have not been hit yet; they move up when they actually happen, with real steps and real output, or get deleted.

---

## Entries

| # | Date | Tool | Task | Steps taken | Expected | Actual | Severity | Workaround | Suggestion |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-09-15 | Alexa+ MCP Toolkit docs | Read the add-on design guide (display modes, tools/schema/data) linked from the docs home | Followed the design-guide links from the MCP Toolkit overview page (record the exact URLs and the HTTP status on the next visit; an entry without them is worth less) | The pages load | The linked URLs were not reachable | Minor | Designed from the functional-requirements page and the quickstart instead | Fix or remove the dead links on the overview page |

## Candidates (not yet hit)

- Alexa+ add-on developer access is limited to select partners; no simulator access for hackathon participants; an emulated host had to be built.
- No documented way for an add-on to receive Alexa-side context (device modality, locale, timezone) or to be invoked proactively.
- AgentCore Runtime serves the Protected Resource Metadata at a path-shaped URL under the runtime ARN; whether Alexa's client follows `resource_metadata` from `WWW-Authenticate` or only looks at the origin root is unverified.
- AgentCore Policy temporal quotas (25 policies per engine, 3 operators per policy, 24-hour window) versus a constitution's `ask` classes; changing temporal policies returns 409 on open sessions. Designed around with one generic temporal permit per TTL.
- Dogwood CLI: documented subcommands (`validate`, `replay`, `lower`, `check-parse`) and a Rust `Authorizer`, no Python bindings; whether the CLI accepts a schema, entities, and an event trace from a subprocess and returns a decision per request is unverified until `ROADMAP.md` item 7.
- AgentCore Runtime cold start: a new session is a fresh microVM, so the first Alexa call after an idle gap cannot meet the 500 ms round-trip requirement; measure and record the figure in Phase 7 (`ROADMAP.md` item 38). Related: the Runtime exposes only the invocation path, so the companion API and Ring webhooks needed a separate always-on service (ADR-008).
- No local library performs Cedar automated-reasoning analysis (always-allow, never-satisfiable); `cedarpy` evaluates only. The analysis exists in AgentCore Policy via `validationMode` on create/update, so it is AWS-mode only.
- Ring sandbox: webhook signature details and synthetic-device event coverage; whether sandbox credentials are issued without a physical Ring device (the getting-started page lists "at least one Ring device for testing" as a prerequisite); partner-initiated OAuth is invitation-only, so the linking flow is the Ring-driven HMAC-nonce pattern.
- Smartcar sandbox versus Tesla Fleet API onboarding cost for a non-fleet developer.

---

## Feature requests

Priority per Devpost: `Critical`, `Important`, `Nice-to-have`.

| Request | Impact | Priority |
|---|---|---|
| Add-on context in `_meta` on every tool call: device modality, locale, timezone | Tools cannot tell a voice-only device from a screen; the add-on has to guess or ask | Critical |
| Recognized-speaker identity for MCP add-ons, as classic Skills get via `context.System.person.personId` with `authenticationConfidenceLevel` ([docs](https://developer.amazon.com/en-US/docs/alexa/custom-skills/add-personalization-to-your-skill.html)); the add-on docs define no equivalent | Every tool call carries only the linked account's token, so per-person rules (a teen may not unlock the door) cannot be enforced by voice on a shared Echo; Haven has to route every security approval to the phone instead. A speaker id with a confidence level would let add-ons lower authority per person safely | Critical |
| Proactive add-on invocation or a notifications API | A household agent cannot tell the member a scheduled action came due or an approval is waiting | Important |
| Alexa+ simulator access for hackathon participants | Every entrant builds their own emulated host; none is faithful | Important |
| AgentCore Policy natural-language authoring exposed via API for third-party UIs | A household app could draft Cedar through the same path the console uses | Nice-to-have |
