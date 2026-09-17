# Hackathon Submission Checklist

Build, Ship, Shape: Amazon Developer Hackathon 2026. Submission period 2026-08-31 10:15 PT to **2026-10-23 12:00 PT**. Judging 2026-11-09 to 2026-11-20. Tracks entered: **Alexa+** and, if the item 34 gate passes, **Ring** (the rules say "Identify which Primary Track(s) you are submitting your Project into"). Mini-challenges entered: **AWS Builder** and **Open Source**. "A project can only win one (1) track prize and one (1) mini challenge prize"; nothing stops it entering more than one.

Two-stage judging: Stage One is a pass/fail check that the project fits the track and actually calls the required technology; Stage Two scores four equally weighted criteria (Tech Implementation, Design, Potential Impact, Quality of the Idea), with up to 10 percent bonus from friction-log entries. Judges may judge from the description, images, and video alone, so those three carry the whole case.

---

## Required components

- [ ] **Working project** built with the required tech: a self-hosted MCP server (spec 2025-11-25 or later, Streamable HTTP) actually called by the demo; Ring API actually called (sandbox synthetic devices count).
- [ ] **Public GitHub repo** with all source, assets, run instructions, and `LICENSE` (Apache-2.0) detectable at the root.
- [ ] **Demo video** under 3 minutes, YouTube or Vimeo, public, English, showing the project functioning on the intended surface (the simulator, honestly labeled, plus one labeled clip in the Alexa developer console). No third-party trademarks or copyrighted music. See `docs/demo-script.md`.
- [ ] **Text description** of features and functionality (draft below).
- [ ] **Product feedback** for every tool/API/SDK used (template below).
- [ ] **Track selection**: Alexa+; Ring too only if the access gate in `ROADMAP.md` item 34 passed (otherwise remove Ring from this checklist, the description, the product-feedback list, and the README banner, and keep the twin doorbell).
- [ ] **Mini-challenges**: both.
  - **AWS Builder**: the services and how they are used, in the product-feedback answer: AgentCore Runtime (hosts the MCP server), Gateway + Policy (Cedar/Dogwood compiled from the constitution, temporal approval rule), Memory, Identity (write-capable credentials readable by one Lambda role only), Bedrock (Claude for narration and drafting, the emulator), Strands, KMS (the key that signs home commands; only the Gateway's Lambda may use it), S3 Object Lock (audit anchors), EventBridge Scheduler, App Runner, RDS, CDK.
  - **Open Source**: the rule asks for "a new, **additional** open-source project or [a contribution] to an existing public repository during the hackathon window, **alongside** a primary track submission". Hirz is the primary submission, so Hirz itself does not qualify. The entry is the separate repository from `ROADMAP.md` items 25a and 29a: the add-on conformance checker and the host harness extracted from Hirz's simulator. The form's four fields: **contribution URL**, **project repository URL**, **GitHub username**, and a description of **what it does, how it works, and why it matters** (every entrant builds an emulated Alexa+ host and none is faithful; the checker tells any add-on developer in one command whether their server meets Amazon's published contract). The rules rate "feature addition with tests, bug fix that unblocks other developers, new integration pattern" above "README update, typo fix". The MCP Python SDK User-Agent pull request, if still open, is listed as a small extra and never leads. Dogwood Python bindings are decided after the item 7 gate.
- [ ] **Judge access**: the hosted demo URL in the testing-instructions field (one click seeds a throwaway household on simulated devices only); repo + video; a no-credential run path (`HIRZ_LLM=off`, twin adapters, `compose.demo.yml`) documented in the README; the AWS stack live for the judging window with a read-only console screenshot set in `docs/img/` in case it must be torn down.
- [ ] **Image gallery**: the seven hand-designed screens (plan, verification, doorbell, and scorecard cards; the rule diff, check-in, and unlock approval on the phone); the AWS console screenshots (AgentCore Policy engine with the compiled constitution, a CloudWatch policy decision beside the signed command the home accepted, the KMS key policy showing one role, the Runtime hosting the MCP server); a refused unsigned command (`LINK_REJECTED`); the courier-correlation warning if it is not in the video; the Dad/dishwasher provenance plan; the Cedar view; the Alexa developer-console clip frame; the same cards in a second real MCP Apps host. The video does not tour the console; the gallery is where AWS Builder judges look.
- [ ] **Newly created during the period** statement: repo created 2026-09-15, all code written during the submission window.
- [ ] **AWS promotional credit** requested before **2026-10-21 12:00 PT**.
- [ ] **Forum question** to the organizers about MCP Toolkit or simulator access posted, and the dated answer recorded in `docs/friction-log.md`.

## Optional, worth doing

- [ ] **Friction log entries** (up to 10 percent bonus) and **feature requests**: maintained continuously in `docs/friction-log.md` (see the rule in `CLAUDE.md`). At submission, copy the entries and requests into the Devpost form.

---

## Description (draft)

> **Hirz: house rules for the AI in your home, and your parents'.**
>
> Hirz lets a family decide what Alexa may do on its own, what it must ask about, and what it may never do. It is built for the person who runs the smart home at their own place and at their parents' place. People reported losing $3.5 billion to imposter scams in 2025 (FTC), and 63 million Americans are family caregivers (AARP). Hirz is rules, not care: it does no medication or health monitoring.
>
> **Is it really him?** Mom asks her Echo whether the "Malik" who just called for money is real. Hirz checks the household's own verified records, never anything the caller said, and asks Malik through his own app. He taps "It wasn't me." Hirz does not stop scam calls; it gives Mom one thing to do: ask first. If someone unexpected then turns up at her door, Hirz warns her and tells Malik.
>
> **The household writes the boundary.** Malik says, "From now on, never unlock the door for someone we're not expecting." Hirz drafts the rule and sends it to his phone: one English sentence, a before-and-after line, the compiled policy. He activates it with a passkey. Anyone in the room can propose a rule; only a person on their own phone can activate one. An hour later the rule refuses an unexpected visitor, and the same lock opens for Mom after an approval on a phone, never by voice, because an Echo is a shared device and Alexa does not tell add-ons who is speaking.
>
> **The home itself enforces it.** Every constitution version compiles to Cedar/Dogwood and is enforced in Hirz's deterministic pipeline and again by AgentCore Policy at the AWS tool boundary, with a temporal rule that an approval must precede the action. Only a permit gets a command signed (a KMS key one Lambda role may use), and a small agent in the home, which holds the Home Assistant token so that it never leaves the house, obeys only signed commands. Hirz's own processes hold no credential that can act on a device.
>
> **A real planner over real prices.** A MILP schedules the EV, home battery, HVAC, and appliances against the household's real rate plan, all-in, and live weather, and reports savings against a baseline solved with the same model. Every figure comes from a cited run or from a backtest over a year of price history; simulated devices are a labeled physics twin. Each member's constraint keeps its owner through the plan, the explanation, and the audit row. No model participates in any decision; Alexa narrates the data Hirz returns.
>
> Built on MCP 2025-11-25 (Streamable HTTP, OAuth 2.1 PKCE, MCP Apps following Amazon's add-on design guide), Python and TypeScript, PostgreSQL, Amazon Bedrock, and Amazon Bedrock AgentCore (Runtime, Gateway, Policy, Memory, Identity), KMS, and S3 Object Lock, with an Alexa+ simulator that hosts the real MCP server through an emulated orchestrator because add-on developer access is limited to select partners. The simulator's host harness and an add-on conformance checker are published as a separate open-source project.

**Ring paragraph (include only if the item 34 gate passed), framed in the track's own priority categories:**

> **Ring: access control, caretaking, event-based triggers.** *Access control:* a Ring press is matched to the household's expected arrivals, and the unlock is a governed action on Hirz's own lock (Ring has no lock API): never for an unexpected visitor once the family writes that rule, and otherwise only after an approval on a phone. *Event-based triggers:* a vehicle-classified motion event enriches the arrival context ("a vehicle arrived at 6:58; Mom is expected at 7:00"), and a doorbell that goes offline makes Hirz more cautious about opening the door it can no longer see. *Caretaking:* at a parent's home, an unexpected visitor shortly after a reported scam call raises a warning and notifies the family member Hirz verified. Hirz never identifies a person from video.

## Product feedback (template, one block per tool)

For each of: Alexa+ MCP Toolkit docs and contract; the Alexa+ add-on design guide; MCP Apps SDK (`@modelcontextprotocol/ext-apps`); MCP Python SDK; AgentCore Runtime; AgentCore Gateway + Policy; Dogwood CLI; AgentCore Memory; AgentCore Identity; Amazon Bedrock (Claude, Nova); Strands Agents SDK; AWS KMS; Ring Developer API; Home Assistant API; the community Alexa Skill MCP bridge; Smartcar sandbox; ComEd Hourly Pricing API; Open-Meteo:

- What it was used for.
- What worked well (setup, docs, performance, reliability).
- What needs improvement (errors, missing features, compatibility).
- Onboarding: time from zero to hello world.
- Would build with it again: yes/no and why.

## Judge run instructions (README section to finalize)

0. No install: open the hosted demo link, press **Start demo**. You get your own throwaway household on simulated devices.
1. Local: clone; `docker compose -f compose.demo.yml up -d`; open `http://localhost:3000`.
2. Pick "Mom's Echo" and play the scam check; then pick "Malik's Echo". The demo evening is paused at 17:30. Press play; speak or type the lines from `docs/demo-script.md`.
3. Switch to Echo Dot mode for the voice-only check.
4. `uv run hirz verify-audit` proves the trail; `uv run hirz scenario run scenarios/demo-evening.yaml --headless --assert` proves the numbers.
5. With AWS credentials and `HIRZ_LLM=bedrock`, the same flows use Bedrock and, with the CDK stack, AgentCore Policy, signed commands, and audit anchors.
