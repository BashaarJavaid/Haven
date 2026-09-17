# Digital Twin and Scenario Engine

The twin is how Haven demonstrates every capability end to end with no hardware, and how the scenario corpus doubles as the integration test suite. It is a real subsystem with a real interface, labeled honestly in every surface as `twin`. See `ARCHITECTURE.md` §5.11–§5.12 and [ADR-006](./adr/ADR-006-twin-first-adapters.md).

---

## 1. Design rules

1. **Same interface as real.** A twin adapter implements the same `Protocol` as its real counterpart. Core code cannot tell them apart; only the `source` stamp differs.
2. **Physics-lite, not random.** Numbers come from small models with named parameters so they stay plausible and reproducible. A judge who owns an EV should never see a home charger add 28 percent in half an hour.
3. **Seeded and reproducible.** Every scenario run has a seed; the same seed produces the same trace.
4. **Sim clock.** All twin models advance on `SimClock`, which can run at wall speed, at a multiplier, or jump to a timestamp. The scheduler and the planner use the injected clock, never `datetime.now()` directly.
5. **Mixable.** A household can run real Home Assistant devices and a twin EV at the same time. The registry decides per domain, and `asset_bindings` can override per entity, which is how the demo runs one physical smart plug (the living-room light) inside an otherwise twin `devices` domain.
6. **Real data where it is free.** ComEd prices and Open-Meteo weather are real feeds; the twin consumes them so the optimizer's numbers are grounded in a real tariff and real weather.

---

## 2. Models

### 2.1 Thermal zone

Discrete RC model per zone, 1-minute internal step:

```
T[t+1] = T[t] + dt/C · ( Q_hvac·u[t] + Q_internal(occupants) + Q_solar(irradiance, orientation) − (T[t] − T_out[t]) / R )
```

Parameters per zone: `C` (kWh/°F thermal mass), `R` (°F/kW envelope resistance), `Q_hvac` (kW heating or cooling), coupling to adjacent zones (a small conductance). Defaults are calibrated so a 2,000 sq ft house pre-warms a living room by 4 °F in about 45 minutes at 3 kW, and drifts about 1 °F/hour at a 30 °F outdoor delta. Every parameter is a knob in the scenario file because the physical world always needs tuning a model can't see.

### 2.2 EV battery

`capacity_kwh` (default 75), `soc`, `charger_kw` (default 7.4 for a Level 2 home charger; 11 optional), charge efficiency 0.92, a taper above 80 percent (power scales linearly to 30 percent of max at 100), and `driving` events that subtract energy. Useful derived facts: 34 → 50 percent at 7.4 kW takes about 1 h 45 min; 34 → 62 percent takes about 3 h 10 min. The demo numbers are computed from this model, never typed by hand.

### 2.3 Home battery

`capacity_kwh` (default 13.5), `power_kw` (5), round-trip efficiency 0.90, reserve floor 10 percent, cycle counter for the planner's throughput penalty.

### 2.4 Solar PV

`kw_peak` (default 6), orientation and tilt, clear-sky irradiance from sun position (latitude/longitude from the household address, computed with a small solar-position routine, no external dependency), scaled by Open-Meteo cloud cover. Output feeds the energy balance and the planner's forecast.

### 2.5 Appliances

Named cycle profiles (`dishwasher`: 105 min, 1.2 kWh, noise level; `laundry`: 60 min, 0.9 kWh; `dryer`: 50 min, 2.5 kWh). A start creates a load trajectory and a completion event.

### 2.6 Tariff (when ComEd is not used)

Time-of-use base with configurable peak windows and stochastic spikes, seeded. Day-ahead and real-time series both produced so the planner path is identical to the real feed.

### 2.7 Occupancy and presence

Members have weekly schedules with arrival/departure noise; scenario events override (early arrival, guests). Sleep state per member from a bedtime window and a zone. `who_is_home` and `sleeping_in(zone)` are derived facts the pipeline and the constitution read.

### 2.8 Wearable recovery

A daily recovery score series per member with autocorrelation and scenario overrides ("low recovery Tuesday"). Shaped like Oura's readiness / Whoop's recovery so the real adapters map onto the same field.

### 2.9 Devices: locks, cameras, lights, shades, doorbell

State machines with realistic latencies (lock 1.5 s, camera arm 0.5 s) and failure injection hooks (`fail_next: unlock`). Doorbell presses carry a stock snapshot image and an optional `expected_visitor` hint the scenario provides; Haven never identifies people from images, so the twin doesn't either.

### 2.10 Contacts and calls

A scenario can inject an inbound-call event with a presented number and a transcript summary (this is what the member relays to Alexa), and can script the trusted contact's response to a check-in (confirm, deny, no answer, delay).

---

## 3. Scenario DSL

```yaml
id: demo-evening
seed: 20261013
household: constitutions/quinn-home.yaml            # household graph + constitution seed
clock: {start: "2026-10-13T17:30:00-05:00", speed: 60}
adapters: {devices: twin, ev: twin, energy: real, wearable: twin, calendar: twin, doorbell: twin, contacts: twin}
bindings: {light.living_room: ha}                      # one physical smart plug; falls back to twin if the device is absent
initial:
  ev: {soc: 0.34, plugged_in: true}
  battery: {soc: 0.55}
  zones: {living_room: {temp_f: 68}, guest_room: {temp_f: 67}}
  presence: {home: [malik], sleeping: []}
timeline:
  - at: "17:30"   ; event: presence.arrive        ; member: malik ; note: "earlier than usual"
  - at: "17:31"   ; event: voice                  ; member: malik ; text: "What's going on tonight?"
  - at: "17:33"   ; event: voice                  ; member: malik ; text: "Do it, but don't charge the car past 50. I'm not driving tomorrow."
  - at: "18:00"   ; event: tariff.spike           ; multiplier: 2.4 ; until: "21:00"      # only if energy: twin
  - at: "18:15"   ; event: call.inbound           ; presented_number: "+1 312 555 0199" ; claim: "Dad stranded, send money to a friend"
  - at: "18:16"   ; event: voice                  ; member: malik ; text: "Send five hundred dollars to this number, it's for Dad, he's stranded."   # a request to act; DENY_CONSTITUTION, then Protect
  - at: "18:16"   ; event: voice                  ; member: malik ; text: "Check with him."
  - at: "18:18"   ; event: contact.checkin_reply  ; member: dad ; reply: confirm_fine
  - at: "19:04"   ; event: doorbell.press         ; expected_visitor: mom
  - at: "19:04"   ; event: voice                  ; member: malik ; text: "That's my mom, let her in."
  - at: "19:05"   ; event: app.approve            ; member: malik ; class: security.door_unlock   # security is never approved by voice
  - at: "22:40"   ; event: voice                  ; member: dad   ; text: "Don't run the dishwasher tonight, I'm working in the kitchen until eleven."
  - at: "23:05"   ; event: presence.sleep         ; member: mom ; zone: guest_room
  - at: "23:30"   ; event: voice                  ; member: malik ; text: "Optimize energy tonight."      # appliance_start after 22:00 is ASK under quinn-home
  - at: "23:31"   ; event: voice                  ; member: malik ; text: "Yes."                          # voice approval is allowed for non-security classes
  - at: "+1d 06:45" ; event: wearable.recovery    ; member: malik ; score: 41
  - at: "+1d 07:00" ; event: voice                ; member: malik ; text: "Good morning."
assert:
  audit_sequence_includes:
    - PLAN_CREATED
    - EXECUTE:energy.hvac_adjust
    - EXECUTE:energy.battery_dispatch
    - PLAN_REVISED                       # after "don't charge past 50"
    - DENY_CONSTITUTION:finance.transfer_money
    - VERIFY
    - VERIFIED
    - EXECUTED:environment.lights        # living-room lamp on at 18:55 for Mom's arrival; the physical plug when bound
    - ASK_CONSTITUTION:security.door_unlock
    - APPROVED
    - EXECUTED:security.door_unlock
    - EXECUTED:security.door_lock
    - PLAN_REVISED                       # after Dad's kitchen constraint
    - ASK_CONSTITUTION:energy.appliance_start   # the household's own rule: ask outside 07:00–22:00
    - APPROVED                           # by voice; appliance_start is not a security class
    - EXECUTED:energy.ev_charge
    - EXECUTED:energy.appliance_start    # 04:30, after Dad's constraint and Malik's approval
  plan_summary:
    peak_kwh_avoided: {min: 5.0}
    estimated_savings_usd: {min: 0.50, max: 3.00}   # provisional; ROADMAP item 17 derives the range from real ComEd data and replaces it
    comfort_violations_minutes: {max: 0}
  ev_soc_at: {"+1d 06:30": {min: 0.50}}
  never:
    - EXECUTE:finance.*
    - EXECUTE:security.access_code_share
```

Event kinds: `voice`, `app.approve|deny` (a member acting in the companion app; the only way a `security.*` approval can happen), `presence.arrive|leave|sleep|wake`, `calendar.add|remove`, `tariff.spike|update`, `weather.update`, `ev.drive|plug|unplug`, `call.inbound`, `contact.checkin_reply`, `doorbell.press|motion`, `device.fail`, `wearable.recovery`, `constitution.activate`, `clock.jump`.

`voice` events are delivered to the simulator's emulated host (or, in headless test mode, to a scripted host that calls the tools the emulator would call, so tests don't need Bedrock).

---

## 4. Running scenarios

```
haven scenario run scenarios/demo-evening.yaml --speed 60            # interactive, companion app follows along
haven scenario run scenarios/demo-evening.yaml --headless --assert   # CI: scripted host, asserts audit + numbers
haven scenario step scenarios/demo-evening.yaml --to "18:16"         # pause before the interruption for recording
```

Scenario runs are recorded (`scenario_runs`) with the seed, the adapter mix, and the resulting audit range, so a demo video can cite the exact run it shows.

**Numbers are derived, never typed.** The demo household is on ComEd's hourly real-time tariff, whose cheap-to-ordinary spread is a few cents per kWh, so the flexible load in the demo (about 12 kWh of EV charging, one home-battery cycle, a dishwasher, HVAC pre-conditioning) yields a nightly dollar saving on the order of $0.50 to $3.00, not the single-digit dollars a steep time-of-use tariff would give. The assertion range in `plan_summary` is provisional until `ROADMAP.md` item 17 derives it from at least two weeks of recorded ComEd day-ahead and 5-minute data run through the planner on the demo loads; the derivation script and its data are kept in `scripts/` so the range is reproducible. `peak_kwh_avoided` is listed first because it is the headline the scorecard leads with. The `tariff.spike` event remains a twin-only test of the planner under a price spike and is never used to inflate a demo number.

---

## 5. Labeling

Every observation carries `source`, one of three values. `real`: a live feed or a physical device (ComEd, Open-Meteo, the smart plug through Home Assistant, Smartcar, Ring sandbox events). `real API, demo devices`: Home Assistant's demo integration, a real API over simulated entities, never shown as plain `real`. `twin`: Haven's own models. The web app shows the badge on every source. The MCP `get_household_context` output (scope `energy` or `environment`) includes the same labels in `data.sources`. The demo video shows the badges; honesty here is a scoring asset, not a liability.
