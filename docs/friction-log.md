# Friction Log

Every friction point hit while building Hirz against a third-party tool, API, SDK, doc, or CLI. Devpost awards up to a 10 percent judging bonus for these, applied at Stage One, so this is the cheapest score in the project. Entries are facts from a session: the doc URL, the exact error text, the date. Nothing invented, nothing padded. A short log of real entries beats a long one.

**Rule:** log at the moment friction happens, not at the end of the session. Trigger: a tool did not do what its docs said, cost more than about 15 minutes, or forced a workaround. Fields are the ones Devpost requires. Severity: `Blocker` (could not proceed without a workaround), `Major` (lost more than an hour or changed the design), `Minor` (annoyance, documented anyway).

Candidates are things expected to bite that have not been hit yet; they move up when they actually happen, with real steps and real output, or get deleted.

---

## Entries

| # | Date | Tool | Task | Steps taken | Expected | Actual | Severity | Workaround | Suggestion |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-09-17 | Alexa+ MCP Toolkit / simulator | Test account linking and MCP App rendering on the real Alexa+ surface | Read the docs ("Category SDK and MCP Toolkit are available to select partners only," [MCP Toolkit overview](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-overview.html), checked 2026-09-16); posted the question on the hackathon forum | Either toolkit/simulator access for participants, or an explicit confirmation there is none | Organizer reply, 2026-09-17: "No, there is no way for participants to get access to the toolkit or simulator. A self-built simulator or other front end for demoing are certainly options though!" | Minor | None needed — ADR-007 already committed to a self-built emulated host (the Hirz Simulator) as the primary demo surface before this answer; the reply confirms that path is the one Amazon expects, it doesn't change it | Ship toolkit/simulator access for hackathon participants (tracked below) |
| 2 | 2026-09-17 | Homebrew in the agent filesystem sandbox | Inspect and install Phase 0 tooling | Ran Homebrew inventory commands; see [Homebrew filesystem and cache settings](https://docs.brew.sh/Manpage) | Read installed tool versions | `Error: Operation not permitted @ dir_s_mkdir - /Users/bashaarjavaid/Library/Caches/Homebrew`; disabling API use instead attempted a tap and failed with `fatal: could not create work tree dir '/opt/homebrew/Library/Taps/homebrew/homebrew-core': Operation not permitted` | Minor | Ran the already-authorized installation through sandbox escalation; uv, pnpm, and Node 24 installed successfully. This was a sandbox permission limitation, not a Homebrew defect. | Document that inventory commands can need writable cache or tap directories in restricted environments |
| 3 | 2026-09-17 | pnpm / typescript-eslint | Resolve compatible scaffold tooling | Added latest stable tooling, then ran `pnpm peers check`; see [typescript-eslint dependency requirements](https://typescript-eslint.io/users/dependency-versions/) | A mutually compatible TypeScript/linter toolchain | `✕ unmet peer typescript`, `Installed: 7.0.2`, `">=4.8.4 <6.1.0"` required by `typescript-eslint@8.70.0` | Minor | Selected TypeScript 6.0.3, pinned it exactly, and reran the peer check: `No peer dependency issues found` | Surface the supported TypeScript range alongside installation instructions |
| 4 | 2026-09-17 | pnpm exact dependency saving | Pin Node type declarations | Used `pnpm add -DwE` with `@types/node@24`, then `@types/node@24.13.5`; see [save-exact](https://pnpm.io/cli/add#--save-exact--e) | An exact direct dependency as requested by `--save-exact` | The manifest retained `"@types/node": "^24.13.5"` after both commands; no CLI error was emitted | Minor | Set `"24.13.5"` explicitly in the manifest and regenerate the lockfile | Make `--save-exact` behavior consistent when a version is supplied explicitly |
| 5 | 2026-09-17 | FastAPI / Starlette TestClient | Test the Phase 0 liveness endpoint with the approved httpx dependency | Followed the [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/) using FastAPI 0.141.1, Starlette 1.6.0, and httpx 0.28.1 | A supported TestClient using the guide's httpx installation | Tests passed but emitted ``StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.`` and `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.` | Minor | Exercise the ASGI app directly with the already-approved httpx.AsyncClient and ASGITransport; no new dependency | Update the testing guide to match the current TestClient dependency transition |

An earlier entry dated 2026-09-15 about unreachable design-guide links was removed on 2026-09-17: the pages loaded on 2026-09-16, and the entry had no URL and no HTTP status, so it did not meet this file's own rule.

## Candidates (not yet hit)

- No documented way for an add-on to receive Alexa-side context (device modality, locale, timezone) or to be invoked proactively.
- AgentCore Runtime serves the Protected Resource Metadata at a path-shaped URL under the runtime ARN; whether Alexa's client follows `resource_metadata` from `WWW-Authenticate` or only looks at the origin root is unverified.
- AgentCore Policy temporal quotas (25 policies per engine, 3 operators per policy, 24-hour window) versus a constitution's `ask` classes; changing temporal policies returns 409 on open sessions. Designed around with one generic temporal permit per TTL.
- Dogwood CLI: documented subcommands (`validate`, `replay`, `lower`, `check-parse`) and a Rust `Authorizer`, no Python bindings; whether the CLI accepts a schema, entities, and an event trace from a subprocess and returns a decision per request is unverified until `ROADMAP.md` item 7.
- AgentCore Runtime cold start: a new session is a fresh microVM, so the first Alexa call after an idle gap cannot meet the 500 ms round-trip requirement; measure and record the figure in Phase 7 (`ROADMAP.md` item 38). Related: the Runtime exposes only the invocation path, so the companion API and Ring webhooks needed a separate always-on service (ADR-008).
- No local library performs Cedar automated-reasoning analysis (always-allow, never-satisfiable); `cedarpy` evaluates only. The analysis exists in AgentCore Policy via `validationMode` on create/update, so it is AWS-mode only.
- Ring sandbox: webhook signature details and synthetic-device event coverage; whether sandbox credentials are issued without a physical Ring device (the getting-started page lists "at least one Ring device for testing" as a prerequisite); partner-initiated OAuth is invitation-only, so the linking flow is the Ring-driven HMAC-nonce pattern.
- Smartcar sandbox versus Tesla Fleet API onboarding cost for a non-fleet developer.
- Home Assistant long-lived access tokens cannot be scoped (a token inherits the creating user's full permissions; [feature request open since 2020](https://community.home-assistant.io/t/support-for-permissions-on-long-lived-access-tokens/190504)); the `system-read-only` group exists but can be assigned only by editing `.storage/auth`. Designed around with a home-side agent that keeps the token in the house (ADR-009).
- The community Alexa Skill MCP bridge has no OAuth account linking and always returns `visual: null`, so identity and MCP App cards cannot be exercised through the Alexa developer console (ADR-007).
- The add-on design guide gives a 768×480 base canvas and a 1.667 scale for Echo Show 8 and 15 but no per-device viewport table; confirm when the cards are built.

---

## Feature requests

Priority per Devpost: `Critical`, `Important`, `Nice-to-have`.

| Request | Impact | Priority |
|---|---|---|
| Add-on context in `_meta` on every tool call: device modality, locale, timezone | Tools cannot tell a voice-only device from a screen; the add-on has to guess or ask | Critical |
| Recognized-speaker identity for MCP add-ons, as classic Skills get via `context.System.person.personId` with `authenticationConfidenceLevel` ([docs](https://developer.amazon.com/en-US/docs/alexa/custom-skills/add-personalization-to-your-skill.html)); the add-on docs define no equivalent | Every tool call carries only the linked account's token, so per-person rules (a teen may not unlock the door) cannot be enforced by voice on a shared Echo; Hirz has to route every security approval to the phone instead. A speaker id with a confidence level would let add-ons lower authority per person safely | Critical |
| Proactive add-on invocation or a notifications API | A household agent cannot tell the member a scheduled action came due or an approval is waiting | Important |
| Alexa+ simulator access for hackathon participants | Participants have no simulator access, so each builds an emulated host to test against. Hirz's host harness and an add-on conformance checker are published as a separate open-source project so the next developer does not start from zero | Important |
| AgentCore Policy natural-language authoring exposed via API for third-party UIs | A household app could draft Cedar through the same path the console uses | Nice-to-have |
