<!-- STATUS: DRAFT baseline for one-by-one verification. Source: Link G4X XtremeX Quick Start Guide (Installer I/O Table + A/B loom pin diagram). Engine: 1993 Celica GT-Four ST185, 5S-GTE turbo. Date: 2026-07-01 -->
<!-- UPDATE 2026-09-05: fully reconciled against XTREMEX-IO-TABLE.html (2026-07-13, authoritative
     per DOCS-CLEANUP-PLAN.md section 7). All channel sections — Trigger, Temp, An Volt, Knock, DI,
     Injection, Ignition, Aux — now match it. The An Volt map previously disagreed on 10 of 11
     channels; that is fixed. Wire colours were dropped rather than carried over (they belonged to
     the old channel numbers); conflict C11 remains open. The injector-impedance conflict is
     resolved (2026-09-05): high impedance / saturated, per ATS. -->
# Link G4X XtremeX — I/O Assignment Table (ST185 5S-GTE)

This is the master pin/channel plan for the **XtremeX** wire-in ECU. It keys off the XtremeX
Quick Start Guide "Installer I/O Table" and the A/B loom diagram (channel name + loom + wire color —
Link assigns functions to these **named channels** in PCLink, not to bare pin numbers).

**Status key:** ✅ assigned (already in CAN/wiring docs) · 🟡 proposed (typical 5S-GTE — confirm) · ⬜ TBD (verify one-by-one)

---

## CAN plan (important)
- **User CAN 1 = the 6-pin Comms/Tuning port** (CAN **H = white**, CAN **L = green**). **All peripheral CAN devices live here**, 1 Mbit/s: center cluster, ECUMaster switchboard, RealDash (listen-only), and the **external lambda controller**.
- **CAN 2 (optional, shares DI 9 on the A loom / DI 10 on the B loom) — left UNUSED.** This keeps DI 9/10 free as digital inputs and puts everything on one bus, as requested.

| CAN device | Frames | Dir |
|---|---|---|
| Center cluster (ESP32-P4) | 0x3E8–0x3EB, 0x3EE (from ECU); 0x3EC/0x3ED (to ECU) | both |
| RealDash (Pi) | 0x3EF, 0x3F0, 0x3F1 | listen-only |
| ECUMaster switchboard | 0x640–0x642 (to ECU); 0x643 (from ECU) | both |
| **External lambda controller** | 0x3B6 (950) Link CAN-Lambda → ECU (fills Lambda 1; ECU re-broadcasts on 0x3EA) | to ECU |

---

## Inputs

**Reconciled 2026-09-05** — Trigger / Temp / An Volt / Knock now match `XTREMEX-IO-TABLE.html`
(2026-07-13, authoritative per `DOCS-CLEANUP-PLAN.md` §7). The previous rows were the stale
2026-07-01 cable-throttle draft and disagreed on 10 of 11 An Volt channels. The **Loom / wire
color** column has been dropped rather than carried over: those colours were tied to the old
channel numbers, and re-attaching them here would invent data. `SCHEMATIC-WIRING.html` pins only a
subset; conflict **C11** (read colours off `XtremeXQuickstartGuide.pdf`) is still open.

| XtremeX channel | Function (ST185 5S-GTE, DBW) | Status | Note |
|---|---|---|---|
| Trigger 1 | Crank (reluctor / VR) | ✅ | 36-2 toothed crank wheel |
| Trigger 2 | Cam (Hall, single tooth) | ✅ | RacerX / Cherry kit |
| Temp 1 | ECT (coolant) | ✅ | built-in pull-up |
| Temp 2 | IAT — manifold | ✅ | built-in pull-up |
| Temp 3 | Oil temp | ✅ | 1k pull-up |
| Temp 4 | Charge-pipe IAT #2 (heat-soak) | ✅ | built-in pull-up — no external resistor. Fuel temp is **not** here; it comes from the flex sensor on DI 2 (conflict C14). |
| An Volt 1 | MAP | ✅ | +5V |
| An Volt 2 | ETB throttle position — **MAIN** | ✅ | Bosch ETB |
| An Volt 3 | ETB throttle position — **SUB** | ✅ | Bosch ETB |
| An Volt 4 | Accelerator pedal (APS) — **MAIN** | ✅ | DBW |
| An Volt 5 | Accelerator pedal (APS) — **SUB** | ✅ | DBW |
| An Volt 6 | Oil pressure | ✅ | |
| An Volt 7 | Fuel pressure | ✅ | |
| An Volt 8 | Coolant pressure | ✅ | |
| An Volt 9 | Fuel level sender | 🟡 | resistive sender needs a divider pull-up on An Volt; calibrate V→% table (points TBD) |
| An Volt 10–11 | spare | ⬜ | wideband is on CAN, not analog (conflict C19) |
| Knock 1 | Knock sensor | ✅ | |
| Knock 2 | spare | ⬜ | |

> **Do not wire An Volt from any older document.** Conflict **C26**: the superseded FuryX map put
> the pedal on An Volt 3/4 and the throttle on An Volt 5/6, which swaps a pedal signal for a
> throttle signal. The rows above are the correct pairing.

**DI section corrected 2026-09-04** — the previous DI 1–10 rows here were a stale cable-throttle-era
draft (2026-07-01) with different channel assignments and no DBW hardware; see git history for that
version. This table now matches `XTREMEX-IO-TABLE.html` (2026-07-13, current). Loom pin / wire color
for these channels is not fully mapped in Markdown yet — `SCHEMATIC-WIRING.html` pins only a subset
(e.g. Aux 2 = A20, ETB motor = B18/B26); do not infer colors from the old table.

| XtremeX channel | Function (ST185, DBW) | Status | Note |
|---|---|---|---|
| DI 1 | Turbo speed (frequency) | ✅ | |
| DI 2 | Flex-fuel sensor (Continental 3-pin) → ethanol% + fuel temp | ✅ | fuel temp comes from here — no separate sensor |
| DI 3–6 | ABS wheel speed ×4 (reluctor) | 🟡 | shielded TP; conditioner if low-speed dropout; drops first |
| DI 7 | Start request (button/key) | 🟡 | ECU-controlled start |
| DI 8 | Clutch switch | 🟡 | ECU-direct (flat-shift/launch latency) |
| DI 9–10 | spare | ⬜ | (CAN2 unused) |
| Brake switch | SB → CAN → ECU | ✅ | cruise cancel |
| Reverse switch | SB → CAN → ECU | ✅ | ECU sets Gear = 7 (R) on 0x3EB via a PCLink Trigger → cluster shows "R" (cluster remaps 7→−1). RealDash also reads this byte directly (added 2026-09-04) to drive a reverse-camera auto-switch — see `CAN-CONFIG-STATUS.md`. |
| Cruise on/off + set/res ladder | SB → CAN → ECU | ⬜ | resistor ladder on a switchboard analog in |

## Outputs

| XtremeX channel | Function (ST185 5S-GTE, DBW) | Status | Note |
|---|---|---|---|
| Inj 1–4 | Injectors cyl 1–4, sequential | ✅ | 1400 cc — see impedance note below |
| Ign 1–4 | 1ZZ COP coils | ✅ | logic-level trigger |
| Ign 5 | 2nd radiator fan (A/C condenser duty) | ✅ | spare ignition drive used as aux |
| Ign 6 | Oil pressure warning lamp | ✅ | spare ignition drive used as aux |
| Ign 7–8 / Inj 5–8 | spare low-side aux | ⬜ | → PMU/PDM if more capacity needed |

> **Injector impedance — RESOLVED 2026-09-05.** **High impedance (saturated).** ATS's 3S/5S
> top-feed injectors are the balanced Bosch EV14 family, which ATS states are high impedance and
> require the stock low-impedance resistor pack to be deleted. PCLink injector drive = **Saturated**,
> **not** Peak & Hold. The old "peak-and-hold" label was carried forward from the *stock* 3S-GTE
> side-feed injectors, which are genuinely low-Z — that is what the resistor pack served.
> `tune/engine_constants.yaml` and `tune/docs/ENGINE_SPEC.md` were corrected to match.

**Aux section corrected 2026-09-04** — the previous Aux 9/10 rows here said "Unused (cable
throttle)"; the car is actually drive-by-wire (Bosch ETB), and the table below matches
`XTREMEX-IO-TABLE.html` (2026-07-13, current). Drive types: Aux 1–4 low-side only, Aux 5–8
hi/lo, Aux 9–10 H-bridge (ETB). All 10 native Aux channels are now spoken for — extra capacity
beyond that comes from spare Ignition/Injection 5–8 (see rows above), then a PMU/PDM.

| XtremeX channel | Function (ST185, DBW) | Drive | Status | Note |
|---|---|---|---|---|
| Aux 1 | Boost solenoid | low-side | ✅ | active-low |
| Aux 2 | ETB power relay (V-Ethrottle feed) | low-side | ✅ | active-low |
| Aux 3 | Fuel pump relay | low-side | ✅ | active-low |
| Aux 4 | AC clutch/kill (grounds relay coil or amp ACT) | low-side | ✅ | active-low sink; floats when off, no pull-up; confirm exact amp circuit |
| Aux 5 | Engine radiator fan relay | hi/lo | ✅ | |
| Aux 6 | EFI main relay (ECU power hold) | hi/lo | ✅ | keeps ECU powered for DBW key-off reset/cooldown |
| Aux 7 | Speed-out → MRS pump SPD pin (Yel/Wht) | low-side pulse | ✅ | 0–5/12V pulse (~4/rev); direct, no resistor; set speedo-out scaling so pump idles down >~10 km/h |
| Aux 8 | Start relay (ECU-controlled) | hi/lo | ✅ | ECU enables/disables in software (clutch/neutral/anti-restart) — no separate cut relay |
| Aux 9 / 10 | Bosch ETB motor (H-bridge) | H-bridge | ✅ | DBW |

## Power / ground
| Channel | Loom / color | Use |
|---|---|---|
| V-Ethrottle (B connector) | — | Relayed 12–14V ETB H-bridge feed (switched by Aux 2) |
| +5V Out | A / Red | TPS + MAP sensor power |
| +8V Out | A / (A-loom) | 8V sensor power (if used) |
| 14V + | A / (A-loom) | Main ECU battery feed (switched) |
| Ground / Shield-Gnd / Gnd Out | A & B / Black | Sensor grounds, shields |

---

## To finish this table (one-by-one pass)
All channel sections are reconciled against `XTREMEX-IO-TABLE.html` (2026-09-05); channel assignment is no longer an open item here. What remains open: **C11** wire colours (read off `XtremeXQuickstartGuide.pdf`), the **injector impedance** conflict flagged under Outputs, and the fuel-level sender calibration points on An Volt 9.
Still open, per `DOCS-CLEANUP-PLAN.md`: (1) trigger type/pattern, (2) ignition type (COP vs
distributor/wasted), (3) injector size/impedance, (4) which analog volts carry which
pressure/flex/wideband (An Volt map disagrees with the HTML source on 8/11 channels), (5) idle
valve type — likely moot now under DBW, confirm. Fill each row as it's confirmed, then lock the table.
