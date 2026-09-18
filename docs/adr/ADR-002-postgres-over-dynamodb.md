# ADR-002 — PostgreSQL as the graph of record

**Status:** Accepted (2026-09-15); amended 2026-09-17 (Phase 0 foundation)

**Decision:** PostgreSQL 16 stores the household graph, constitution versions, plans, actions, approvals, verification cases, memory proposals, and the audit chain. AgentCore Memory stores conversational short-term memory and extracted long-term preferences. A dedicated graph database is not used.

**Reasoning:**

- The audit ledger is a hash chain per household, with one pointer row per household updated in the same transaction as the insert. That needs transactions and row locks; DynamoDB's conditional writes can approximate it but make the verifier and exports harder and were the wrong fit in the author's earlier gateway work for the same reason.
- The household graph is small (tens of members and assets per household) with a handful of relationship types. Tables plus JSONB attributes and a materialized `household_context` view answer every query the pipeline needs in one round trip. A graph database would add an operational system for expressiveness nothing here requires.
- Row versioning (`valid_from`/`valid_to`) gives "what did Hirz believe at 18:16?" cheaply, which is central to explainability.
- Local development with Docker Compose needs a database that runs identically on a laptop and in AWS. RDS Postgres is that; DynamoDB Local is a weaker mirror.

**Alternatives considered:**

- *DynamoDB single-table.* AWS-native and serverless, attractive for the AWS Builder story. Rejected for the audit chain, the relational plan/approval/action lifecycle, and local-dev fidelity. The AWS story is carried by AgentCore, not by the database.
- *Postgres + Neo4j.* Rejected: no query in the design needs traversal depth beyond two hops.
- *AgentCore Memory as the graph of record.* Rejected: memory is model-extracted and unstructured; the graph must be typed, versioned, and never written by a model. Memory feeds *proposals* that a member accepts into the graph.

**Consequences:** RDS is the one always-on AWS cost, so it is deployed only for the judging window. `household_id` scoping on every table is a convention enforced by a test.


**Phase 0 implementation decisions (author-approved 2026-09-17):** SQLAlchemy Core
with async psycopg and Alembic; no ORM. The initial migration contains only
`households`, `members`, `member_accounts`, `audit_log`, and `audit_pointer` (exact
schema in `ARCHITECTURE.md` §6.1). Household/member identifiers are UUIDs; member
links use composite household-scoped foreign keys. Provider/sub uniqueness is
within each household, allowing the same account to link to both homes.

The single-pointer wording means one pointer **per household**, with a local
sequence and a zero-hash genesis. A global chain was rejected because verification
and exports must be household-scoped. Audit execution remains item 10. Graph
history columns, repositories, and seeds remain item 6; this migration does not
claim historical graph reads. Migrations are explicitly invoked and have a
reversible, destructive downgrade tested only against disposable databases.
