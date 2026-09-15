# ADR-006 — Twin-first adapters: every domain ships real and twin behind one interface

**Status:** Accepted (2026-09-15)

**Decision:** Each adapter domain declares a `Protocol` and ships a real implementation coded against the vendor API and a twin implementation backed by physics-lite models on a simulated clock. The registry selects per domain at startup; every observation carries `source: real | twin`; every surface shows the label. The scenario DSL drives the twin and doubles as the integration test corpus.

**Reasoning:**

- The author owns no Alexa device, EV, wearable, or smart-home hardware, and the product must demonstrate every capability end to end. Mocks would be dismissed; a labeled, reproducible, physically plausible twin is a product feature (onboarding preview, what-if planning, safe testing of a new constitution).
- Real data where it is free keeps the twin grounded: ComEd prices and Open-Meteo weather are live; Home Assistant's demo integration provides real device semantics; Smartcar's sandbox and Ring's sandbox exercise the real API code paths.
- The same interface means buying a smart plug later is a configuration change, and a mixed real/twin household is a first-class configuration.
- Honest labeling converts a weakness into credibility with judges and, later, with customers.

**Alternatives considered:**

- *Hardcoded demo fixtures.* Rejected: numbers drift from physics, tests don't exercise real code paths, and the demo reads as fake.
- *Real hardware purchases.* Out of budget and would still leave EV, battery, and solar unrepresented.
- *Home Assistant only.* Good device layer, but no EV/battery/solar/wearable/contacts models and no scenario timeline; kept as the device adapter, not the twin.

**Consequences:** Twin models carry explicit calibration knobs and physics tests. The pipeline treats twin observations like real ones but the `state_stale` factor and verify-after-act apply equally, so a lying twin is caught the same way a flaky sensor would be.
