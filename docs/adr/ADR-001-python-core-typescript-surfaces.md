# ADR-001 — Python core, TypeScript surfaces

**Status:** Accepted (2026-09-15)

**Decision:** Haven Core (graph, constitution, risk, pipeline, planner, executor, protect, adapters, twin, MCP server, companion API) is Python 3.12 on FastAPI and the official `mcp` SDK. The MCP App cards, the companion web app, the simulator, and the AWS CDK stack are TypeScript.

**Reasoning:**

- The official MCP Python SDK is first-party and AgentCore Runtime's MCP hosting contract is documented against FastMCP on port 8000 at `/mcp`. The author's prior MCP work (PortunusMCP, MCP-Sentinel) is Python, so the audit ledger, ABAC-style grammar, and fail-closed patterns port directly.
- The planner needs `scipy.optimize.milp` (HiGHS); the Python scientific stack is the natural home for the twin's physics models too.
- MCP Apps are built with `@modelcontextprotocol/ext-apps`, a TypeScript SDK with React hooks and a host-bridge implementation the simulator needs. Rewriting a host bridge in Python for a browser surface would be fighting the ecosystem.
- Amazon's own Alexa+ tooling (`@alexa-ai/cli`) and the Ring samples are Node; CDK's first-class language is TypeScript.

**Alternatives considered:**

- *All TypeScript.* One language, and the TS MCP SDK is excellent. Rejected because the planner and twin would need a JS MILP solver (weaker options) and the author's tested security patterns are Python.
- *All Python.* Rejected because the MCP App host bridge and a credible React companion app are the demo; hand-rolled HTML would cost the Design criterion.

**Consequences:** Two toolchains (`uv`, `pnpm`), two lint/type stacks, and one shared contract: the tool catalog's `outputSchema`s are generated from the Pydantic models into TypeScript types so cards and server cannot drift.
