# ADR-007 — Build to the real add-on contract; demo through an emulated host; Skill bridge later

**Status:** Accepted (2026-09-15)

**Context:** Alexa+ add-on development is currently available to select partners working directly with Amazon. The hackathon rules explicitly accept "a self-hosted MCP server (spec 2025-11-25 or later, Streamable HTTP) or an Agent Skill, or a simulated experience" and say participants "can simulate experiences via web app". The author has no add-on access and no Alexa+ device.

**Decision:** Haven's MCP server is built to the published add-on contract verbatim (Streamable HTTP, OAuth 2.1 PKCE S256, Protected Resource Metadata, `401` challenge, MCP Apps for visuals, tool and UX functional requirements, latency budget). The primary demo surface is the **Haven Simulator**: a browser host that runs a genuine MCP client (a Strands agent on Bedrock Nova Lite) against the genuine server, implements the MCP Apps host bridge, provides voice in/out, and switches between Echo Show and Echo Dot behavior. It is labeled as an emulation. A physical-Echo path through a classic Alexa Skill bridging to the MCP server is documented for when a device is available.

**Reasoning:**

- Building to the contract means the day access opens, the work is `alexa-ai new mcp`, metadata, and certification, not a rewrite. Every contract item is a test.
- An emulated host that actually speaks MCP to the real server proves more than a scripted video: the tool calls in the transcript are real.
- Nova Lite is the closest available stand-in for the orchestrator class Alexa+ runs on, and the community Alexa-Skill-MCP bridge already uses it for the same reason.
- The simulator is also the product's own test bench and the fallback surface for any MCP-capable assistant.

**Alternatives considered:**

- *Wait for add-on access.* Not available on the hackathon timeline.
- *Alexa Skill (ASK) with hand-written intents.* Would demonstrate on hardware but would not be an MCP add-on, would not exercise MCP Apps, and would fail the "actually calls the required technology" check for the Alexa+ track as specified.
- *Community Skill bridge on a physical Echo now.* Requires an Echo the author does not own; retained as the Phase 9 path.
- *Claude/ChatGPT as the demo host.* Real MCP Apps hosts, but they are not Alexa and would confuse the track story; useful only as a secondary interoperability check.

**Consequences:** The simulator must be honest (banner, transcript, badges) and must enforce Alexa+'s voice-only and option-count rules so the preview is faithful. `HAVEN_LLM=off` swaps the emulator for a scripted host so CI and credential-less judges can run the demo.
