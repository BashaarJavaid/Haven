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
- [ ] **Track selection**: Alexa+ primary, Ring.
- [ ] **Mini-challenge**: AWS Builder, with the AWS services and how they are used described in the product-feedback answer.
- [ ] **Judge access**: repo + video; a no-credential run path (`HAVEN_LLM=off`, twin adapters, `compose.demo.yml`) documented in the README; the AWS stack live for the judging window with a read-only console screenshot set in `docs/img/` in case it must be torn down.
- [ ] **Newly created during the period** statement: repo created 2026-09-15, all code written during the submission window.
- [ ] **AWS promotional credit** requested before **2026-10-21 12:00 PT**.

## Optional, worth doing

- [ ] **Friction log entries** (up to 10 percent bonus). Each entry: task attempted, steps, expected vs. actual, severity, workaround, actionable suggestion. Candidates, to be confirmed by what actually happens:
  - Alexa+ add-on developer access gated to select partners; no simulator access for hackathon participants; had to build an emulated host.
  - Alexa+ MCP docs: the design-guide pages (display modes, tools/schema/data) referenced from the docs home were not reachable at the linked URLs on 2026-09-15.
  - No documented way for an add-on to receive Alexa-side context (device modality, locale, timezone) or to be proactively invoked.
  - AgentCore Runtime MCP + Alexa's PRM expectations: how the Runtime's `.well-known` path maps to Alexa's discovery.
  - Cedar temporal policy quotas (25 per engine, 3 operators, 24 h window) versus a constitution's `ask` classes.
  - Ring sandbox: webhook signature verification details, synthetic device event coverage.
  - Smartcar sandbox vs. Tesla Fleet API onboarding cost for a non-fleet developer.
- [ ] **Feature requests** with priority: Alexa+ add-on context in `_meta` (modality, locale, timezone) — Critical; proactive add-on invocation or notifications API — Important; hackathon simulator access — Important; AgentCore Policy natural-language authoring exposed via API for third-party UIs — Nice-to-have.

---

## Description (draft)

> **Haven — the bounded-autonomy operating system for the home.**
>
> Today's smart home follows commands. Haven gives Alexa+ a shared model of the household — its people, roles, trusted contacts, devices, schedules, energy, and preferences — and a **Household Constitution** the family writes that says what Haven may do on its own, what it must ask about, and what it may never do. Every proposed action is classified by a deterministic risk engine, checked against the constitution, checked again at the AWS tool boundary by AgentCore Policy (the constitution compiles to Cedar), executed through adapters, verified by reading the world back, and recorded in a signed audit ledger. Alexa narrates the data Haven returns; Haven never scripts Alexa's speech.
>
> In one evening Haven plans energy across an EV, a home battery, and the thermostat against live utility prices and a guest's comfort preference; re-plans by voice; runs low-risk actions autonomously; refuses a family-impersonation money request and verifies Dad through his own verified channel; gates a door unlock for an expected visitor at a Ring doorbell with an auto-relock; coordinates a second household member's constraint; and reports a daily scorecard. Everything simulated is labeled as a digital twin; prices, weather, Home Assistant device semantics, and the Ring sandbox are real.
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
