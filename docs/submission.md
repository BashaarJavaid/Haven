# Hackathon Submission Checklist

Build, Ship, Shape: Amazon Developer Hackathon 2026. Submission deadline **2026-10-23 12:00 PT**. Judging 2026-11-09 to 2026-11-20. Tracks entered: **Alexa+ (primary)**, **Ring (secondary)**. Mini-challenge: **AWS Builder**. A project can win one track prize and one mini-challenge prize.

Two-stage judging: Stage One is a pass/fail check that the project fits the track and actually calls the required technology; Stage Two scores four equally weighted criteria (Tech Implementation, Design, Potential Impact, Quality of the Idea), with up to 10 percent bonus recommended from friction-log entries. Judges may judge from the description, images, and video alone.

---

## Required components

- [ ] **Working project** built with the required tech: a self-hosted MCP server (spec 2025-11-25 or later, Streamable HTTP) actually called by the demo; Ring API actually called (sandbox synthetic devices count).
- [ ] **Public GitHub repo** `BashaarJavaid/HavenOS` with all source, assets, run instructions, and `LICENSE` (Apache-2.0) detectable at the root.
- [ ] **Demo video** under 3 minutes, YouTube or Vimeo, public, English, showing the project functioning on the intended surface (the simulator, honestly labeled, plus the AWS console). No third-party trademarks or copyrighted music. See `docs/demo-script.md`.
- [ ] **Text description** of features and functionality (draft below).
- [ ] **Product feedback** for every tool/API/SDK used (template below).
- [ ] **Track selection**: Alexa+ primary; Ring only if the access gate in `ROADMAP.md` item 34 passed (otherwise remove Ring from this checklist, the description, the product-feedback list, and the README banner, and keep the twin doorbell).
- [ ] **Mini-challenges**: AWS Builder, with the AWS services and how they are used described in the product-feedback answer; and Open Source (Haven is a new Apache-2.0 project created in the window) with at least one upstream pull request opened during the window cited. Select both if the form allows; a project can win only one, but nothing says it can enter only one.
- [ ] **Judge access**: repo + video; a no-credential run path (`HAVEN_LLM=off`, twin adapters, `compose.demo.yml`) documented in the README; the AWS stack live for the judging window with a read-only console screenshot set in `docs/img/` in case it must be torn down.
- [ ] **Image gallery**: the AWS console screenshots (AgentCore Policy engine with the compiled constitution, a CloudWatch policy decision, the Runtime hosting the MCP server, the worker service), the constitution page, the plan card, and the verification card. The video does not tour the console; the gallery is where AWS Builder judges look.
- [ ] **Newly created during the period** statement: repo created 2026-09-15, all code written during the submission window.
- [ ] **AWS promotional credit** requested before **2026-10-21 12:00 PT**.

## Optional, worth doing

- [ ] **Friction log entries** (up to 10 percent bonus) and **feature requests**: maintained continuously in `docs/friction-log.md` (see the rule in `CLAUDE.md`). At submission, copy the entries and requests into the Devpost form.

---

## Description (draft)

> **Haven — the bounded-autonomy operating system for the home.**
>
> Household agents on Alexa+ share a pattern: an allowlist of actions, a human-approval step, an audit trail. Haven has that baseline and adds four things on top of it.
>
> **The household writes the boundary.** A **Household Constitution**, authored as a form, as YAML, or in plain English, says per action class and per member what Haven may do on its own, what it must ask about, and what it may never do. Every version compiles to Cedar/Dogwood and is enforced twice: in Haven's deterministic pipeline and again by AgentCore Policy at the AWS tool boundary, outside Haven's process, with a temporal rule that an approval must precede the action. **A real planner over real prices.** A MILP schedules the EV, home battery, HVAC, and appliances against live utility prices and weather and reports savings against a baseline solved with the same model; simulated devices are a labeled physics twin. **Multi-member coordination with provenance.** Each member's constraint keeps its owner and time through the plan, the explanation, and the audit row. **Verification from the household's own records.** Trusted contacts have out-of-band verified channels; "is this really Dad?" is answered by the graph and Dad's own app, never by the caller. Alexa narrates the data Haven returns; Haven never scripts Alexa's speech, and no model participates in any decision.
>
> In one evening Haven plans energy across an EV, a home battery, and the thermostat against live utility prices and a guest's comfort preference; re-plans by voice; runs low-risk actions autonomously; refuses the household's own request to send money to a stranded "Dad" under a `never` rule the family wrote, and verifies Dad through his own verified channel (the same flow protects a parent living alone whose Echo is linked to their own Haven); takes a Ring doorbell press, matches it to an expected visitor, and unlocks Haven's own smart lock only after a phone approval, with an auto-relock (Ring supplies the event and snapshot; the lock is a Home Assistant device); coordinates a second household member's constraint; and reports a daily scorecard. Everything simulated is labeled as a digital twin; prices and weather are live feeds, the living-room light is a physical smart plug through Home Assistant, the other Home Assistant devices are its demo integration (real API, simulated devices, labeled as such), and the Ring events come from the Ring sandbox.
>
> Built on MCP 2025-11-25 (Streamable HTTP, OAuth 2.1 PKCE, MCP Apps), Python and TypeScript, PostgreSQL, Amazon Bedrock (Claude, Nova), and Amazon Bedrock AgentCore (Runtime, Gateway, Policy, Memory, Identity), with an Alexa+ simulator that hosts the real MCP server through an emulated orchestrator because add-on developer access is currently limited to select partners.

## Product feedback (template, one block per tool)

For each of: Alexa+ MCP Toolkit docs and contract; MCP Apps SDK (`@modelcontextprotocol/ext-apps`); MCP Python SDK; AgentCore Runtime; AgentCore Gateway + Policy; AgentCore Memory; AgentCore Identity; Amazon Bedrock (Claude, Nova); Strands Agents SDK; Ring Developer API; Home Assistant API; Smartcar sandbox; ComEd Hourly Pricing API; Open-Meteo:

- What it was used for.
- What worked well (setup, docs, performance, reliability).
- What needs improvement (errors, missing features, compatibility).
- Onboarding: time from zero to hello world.
- Would build with it again: yes/no and why.

## Judge run instructions (README section to finalize)

1. Clone; `docker compose -f compose.demo.yml up -d`; open `http://localhost:3000`.
2. The demo evening is paused at 17:30. Press play; speak or type the lines from `docs/demo-script.md`.
3. Switch to Echo Dot mode for the voice-only beat.
4. `uv run haven verify-audit` proves the trail; `uv run haven scenario run scenarios/demo-evening.yaml --headless --assert` proves the numbers.
5. With AWS credentials and `HAVEN_LLM=bedrock`, the same flows use Bedrock and, with the CDK stack, AgentCore Policy.
