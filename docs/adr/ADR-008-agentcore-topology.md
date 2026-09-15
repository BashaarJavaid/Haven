# ADR-008 — AgentCore topology and cost posture

**Status:** Accepted (2026-09-15)

**Decision:** In AWS, the Haven container (MCP server plus Core) runs on **AgentCore Runtime** with `protocol: MCP` and a `CUSTOM_JWT` authorizer backed by a Cognito user pool (PKCE S256). The Executor's action tools are exposed through an **AgentCore Gateway** target (`haven-actions` Lambda) with a **Policy engine** holding the Cedar/Dogwood set compiled from the active constitution; the Executor calls the Gateway with a policy session id so temporal approval rules apply. **AgentCore Memory** holds conversational and extracted-preference memory; **AgentCore Identity** holds outbound adapter credentials; **Bedrock** serves Claude Haiku 4.5 and Sonnet 5 for Haven and Nova Lite for the emulator; **EventBridge Scheduler** plus a tick Lambda drive scheduled actions; **RDS Postgres** is the graph of record; observability flows through AgentCore Observability to CloudWatch. Infrastructure is AWS CDK (TypeScript). Everything except RDS is pay-per-use; the stack is deployed for recording and judging and destroyed after, with a $40 budget alarm.

**Reasoning:**

- The AWS Builder criterion rewards "multi-service pipeline (Bedrock + AgentCore + Strands)" and "agentic architecture with Claude", and penalizes "single Bedrock call". Here AWS operates Haven's enforcement (Policy), state (Memory), identity (Identity), and hosting (Runtime); it is the backbone, not decoration.
- AgentCore Runtime's MCP hosting serves the `401` challenge and the Protected Resource Metadata document, which is exactly what Alexa+ account linking discovers. Cognito supports PKCE S256 and `code_challenge_methods_supported`, satisfying the add-on requirement.
- AgentCore Policy is the only managed service in the design that gives an independent, auditable, temporal enforcement point for the constitution. Its CloudWatch decisions become audit evidence.
- The $150 credit is finite. Pay-per-use services cost cents at demo scale; RDS is the one always-on line item, so it lives only during the judging window. Local Compose is the everyday path.

**Alternatives considered:**

- *ECS Fargate or App Runner for the MCP server.* Simpler ops for a plain FastAPI service, but loses the Runtime's PRM/JWT integration and the "AgentCore runs Haven" story, and Fargate is always-on cost.
- *Lambda for everything.* Streamable HTTP with SSE and stateful elicitation fit poorly on Lambda; rejected.
- *Skip Gateway; evaluate Cedar only in-process.* Cheaper, but then "enforced at the AWS boundary" is untrue. Rejected (see ADR-003).
- *DynamoDB instead of RDS to be fully serverless.* Rejected in ADR-002.
- *Terraform.* Fine, but CDK is TypeScript-native, matches the surfaces' language, and is what Amazon's own Alexa tooling references.

**Consequences:** `haven doctor --aws` must verify PRM, `401`, a Runtime tool call, a Gateway policy decision, and a scheduler tick before any AWS claim appears in the README. Temporal policies require the Gateway role to have `bedrock-agentcore:GetWorkloadAccessToken`, and all AgentCore resources must sit in one account and region (us-east-1). Changing temporal policies invalidates open sessions; activation starts a new plan session.
