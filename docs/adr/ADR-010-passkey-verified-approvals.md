# ADR-010 — Security approvals are proven to the signer by the member's passkey

**Status:** Accepted (2026-09-17); build is `ROADMAP.md` item 38d, below the cut line. Until it is built the docs claim only what holds without it.

**Context:** ADR-009 makes the worker an untrusted relay for commands: it cannot forge one. A second review on 2026-09-17 pointed out that it can still forge the *reason* for one. The temporal permit is satisfied by an earlier `approve_action` response, and that call reaches the Gateway through the worker. A fully compromised worker could call `approve_action` itself, then the action, and receive a signed unlock without any person touching a phone. The README's "only a person on their own phone" was therefore true of the product's normal path and not of the boundary. The first answer was to scope the claim to bugs and bypass paths, which is what the docs now say. This ADR is the stronger answer for the classes where it matters.

**Decision:** For `security.*` classes, `approve_action` at the boundary answers `approved: true` only when it carries a WebAuthn assertion that the `hirz-actions` Lambda verifies itself: the challenge is the action's `content_hash` (recomputed by the Lambda, ADR-009), the credential belongs to a member of the action's household with a role the rule allows, and the key is not revoked. Passkeys are registered through a second small Lambda, `hirz-passkeys`, reached from the browser through its own function URL and never through the worker. It stores public keys in SSM Parameter Store entries that only its role can write and that `hirz-actions` can read. The worker relays the assertion and can neither produce one nor add a key.

**Reasoning:**

- An `ask` class needs an approval whatever the context facts say, so this guarantee does not inherit the limit in ADR-003 (the boundary is not independent about facts). For the door, the chain becomes passkey → verified by the signer → signed → verified in the home.
- The enrollment path is the part that makes it real. Verifying assertions against keys the worker could write would prove nothing, which is why a first version of this idea was rejected the same day.
- It reuses what exists: the companion app already approves security actions under a passkey; the change is who checks it.

**Alternatives considered:**

- *Scope the claim and stop there.* Free, honest, and what the docs do until 38d's `verify:` passes. Kept as the fallback.
- *Verify the assertion in the worker.* Pointless: the worker is the process being distrusted.
- *Pass a fresh Cognito token for the approving member to the Gateway.* Proves a recent sign-in, not consent to this action; nothing binds it to the `content_hash`.
- *DynamoDB for the key store.* Works; Parameter Store is free at this scale and one fewer resource.

**Consequences:** One new Lambda with a function URL and a handful of free-tier parameters, pay-per-use, approved by the author on 2026-09-17. The threat-model row will be **Partial**, not Yes: the approval page is still served by Hirz, so a compromised worker could show one request while asking the passkey to sign another. Serving that page from static hosting the worker cannot change is a Phase 9 item. `auto` classes are unaffected and remain exposed to false context facts by design. Adversarial tests: no assertion, a forged one, one over a different hash, and one from a revoked key each produce no approval event and no signature; the worker's role cannot write a key.
