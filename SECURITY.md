# Security Policy

## Status

Hirz is pre-1.0 and maintained by a single author. It has not been through an external security audit. It controls physical devices and gates security-relevant actions, so read `THREAT_MODEL.md` before connecting it to anything real. Never connect Hirz to life-safety systems.

## Reporting a vulnerability

**Do not open a public issue for a security bug.**

Use GitHub's private vulnerability reporting on `BashaarJavaid/Hirz`, or email **aarish@issm.ai**.

Include the affected component, what an attacker gains, and a reproduction if you have one. Acknowledgement within 7 days; a fix or documented mitigation within 30 days for anything that breaks a guarantee this project actually claims.

## What counts as a vulnerability here

Scope is defined by [`THREAT_MODEL.md`](./THREAT_MODEL.md), which is explicit about what is *not* protected. A report that a documented non-guarantee is not, in fact, guaranteed is not a vulnerability. A report that the threat model **overstates** what the code does absolutely is, and is exactly the kind of report wanted.

In scope:

- Any path that executes an action without a `Decision` and an audit row, or that bypasses a constitution `never`, a risk floor, or the boundary check.
- An approval redeemable for an action whose content or context differs from what was approved.
- Cross-household data access with a valid token for another household.
- A forged or replayed Ring event that Hirz acts on.
- A home device acting on a command that the boundary did not sign: an unsigned, tampered, expired, or replayed command accepted by Hirz Link, or any Hirz process outside the home holding a credential that can act on a device in AWS mode.
- A rule change taking effect from a voice alone, without activation in the companion app.
- A hosted-demo household reaching a real adapter.
- A way to write to, forge, or silently break the audit chain without detection by `hirz verify-audit`.
- Model output influencing a decision (as opposed to narration, drafting, or schema-validated signal extraction).
- A `Decision` Hirz reports that does not match what it enforced.

Out of scope, per the threat model:

- Anything requiring a compromised Hirz host, AWS account, or authorization server.
- Manipulation of Alexa+'s own orchestrator; Hirz treats every tool call as a request from the linked member and gates it accordingly.
- Insider abuse by a legitimate linked adult (attributable after the fact by design, not prevented).
- Physical identification of people from video or audio (Hirz never does this).
