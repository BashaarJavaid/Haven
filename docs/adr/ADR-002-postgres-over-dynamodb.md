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

## Item 6 amendment — 2026-09-18 (author-approved)

The graph uses current tables under stable identity keys plus matching history
tables, with UTC half-open `valid_from`/`valid_to` intervals. Separate identity
and version tables were rejected because the foundation already supplies the
foreign keys. History describes what was recorded then, not retroactive effective
time: backdated household changes are refused, expected `valid_from` tokens
prevent lost updates, unchanged writes are no-ops, and changed versions of one
entity cannot share an instant. Deletion/tombstones and bitemporal corrections
were explicitly deferred. Existing rows begin history at migration time; unknown
rate plans and location remain unknown rather than invented.

Current context reads use `household_context`; historical reads reconstruct from
current/history tables in one query. Materializing every historical snapshot was
rejected to avoid duplicated snapshots and repeated history rebuilds. Writers
serialize before mutation and refresh once in the same transaction. A plain
refresh was chosen over concurrent refresh for this small graph; it replaces the
whole view and can block readers ([PostgreSQL 16 refresh contract](https://www.postgresql.org/docs/16/sql-refreshmaterializedview.html)).
The global lock and refresh are a documented ceiling, not a claim of scaled
throughput. Daily observation-history partitions are deferred until ingestion
volume warrants their maintenance, rather than adding a partition scheduler now.

Item 6 has an explicit **synthetic bootstrap exception** before the pipeline and
signed audit writer exist. The local seed command initializes only `quinn-home`
and `quinn-parents`, with `demo` account links and twin asset bindings; repository
writes are otherwise exercised only in tests. No device action, policy activation,
runtime mutation endpoint, or fabricated audit event is authorized by this
exception. Existing/evolved households are never reset. Constitution versions
are persisted unvalidated, with no compiled policy or activation timestamp;
item 7 owns semantic validation. Multi-document YAML preserves the constitution's
specified top-level shape; nested wrappers and separate graph files were rejected.

The complete graph entity set is implemented now, including `shade` to reconcile
§5.1 with the existing device/context specs. Five graph-backed context scopes ship;
planner/constraint/security summaries, passkeys, adapters, and rule evaluation
remain with their owning items. Public snapshots exclude account subjects,
channel values/hashes, and safe-word hashes at the SQL projection; private reads
stay in explicitly household-scoped repositories. Only availability failures may
serve a process-local cached current snapshot, with an explicit read-only opt-in
and stale labeling. Historical reads and decision callers fail closed.

The approved synthetic contents and loader contract are documented in
[the constitution spec](../constitution.md#21-action-classes) and
[development procedures](../development.md). They grant Malik no membership or
login in his parents' home. The decisions in this amendment supersede only the
corresponding graph target-state details; threat-model rows remain unearned.

## Item 9 amendment — 2026-09-18

The approved internal pipeline uses three additional household-scoped tables:
`actions` (immutable proposal/requester/cost and grant reference), `approvals`, and
`approval_votes`. Decisions and dollar reservations stay in the signed audit ledger;
separate decision, budget-counter and execution-queue tables were rejected as
unnecessary. The existing graph transaction lock precedes approval and audit pointer
row locks, so single redemption, budget reservation and graph changes commit together.
The global serialization ceiling remains intentional pending measured contention.

The signed append primitive is pulled forward from item 10 because an item 9 grant
cannot safely commit without its audit row. The verifier, export and 100-concurrent-
decision gate stay in item 10. “One execution” in item 9's existing verification
sentence means **one durable execution authorization**, not device actuation; the
executor remains item 19. Dollar estimates reserve on grant; settlement/refunds and
per-class action-count limits are explicitly deferred. A second counter subsystem
or pretending that an ASK reserved spend was rejected.

Canonicalization uses the approved [Trail of Bits RFC 8785 implementation](https://github.com/trailofbits/rfc8785.py),
not `canonicaljson` (which was incorrectly named as RFC 8785). Exact envelope and
hashing contracts are in [architecture §3.4 and §5.10](../../ARCHITECTURE.md#34-internal-pipeline-contract-item-9).
Neither migrations nor the pipeline initialize or replace signing credentials.
