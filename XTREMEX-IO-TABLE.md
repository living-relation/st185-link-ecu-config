<!-- STATUS: DRAFT baseline for one-by-one verification. Source: Link G4X XtremeX Quick Start Guide (Installer I/O Table + A/B loom pin diagram). Engine: 1993 Celica GT-Four ST185, 5S-GTE turbo. Date: 2026-07-01 -->
<!-- UPDATE 2026-09-04: DI and Aux sections corrected to match XTREMEX-IO-TABLE.html (2026-07-13,
     current — drive-by-wire, not cable throttle). Trigger/Temp/An Volt/Knock/Injection/Ignition
     sections below are still the stale 2026-07-01 draft; per DOCS-CLEANUP-PLAN.md this doc's
     An Volt map disagrees with XTREMEX-IO-TABLE.html on 8 of 11 channels and has not been
     reconciled yet. Do not treat this file as fully current outside DI/Aux. -->
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

| XtremeX channel | Loom / wire color | Function (ST185 5S-GTE) | Status |
|---|---|---|---|
| Trigger 1 | A / Yellow | Crank position (Ne) | 🟡 confirm trigger type/pattern |
| Trigger 2 | A / Yellow-Brown | Cam / home (G) | 🟡 confirm |
| Temp 1 | A / Red-White | ECT (coolant temp) | ✅ |
| Temp 2 | A / Green | IAT (intake air temp) | ✅ |
| Temp 3 | B / Yellow-Green | Oil temp | ✅ |
| Temp 4 | A / Yellow-Orange | Fuel temp (or from flex sensor) | ⬜ |
| An Volt 1 | A / Red | MAP sensor | ✅ |
| An Volt 2 | A / (A-loom) | TPS (throttle position) | ✅ |
| An Volt 3 | A / Green | Oil pressure | ✅ |
| An Volt 4 | A / (A-loom) | Fuel pressure | ✅ |
| An Volt 5 | B / Green | Coolant pressure | ✅ |
| An Volt 6 | B / Yellow-Green | Charge-pipe IAT (2nd, if analog) | ⬜ |
| An Volt 7 | B / (B-loom) | Wideband (only if analog 0–5V type) | ⬜ depends on lambda choice |
| An Volt 8 | B / (B-loom) | spare | ⬜ |
| An Volt 9 | A / White-Green | spare | ⬜ |
| An Volt 10 | A / White-Blue | spare | ⬜ |
| An Volt 11 | A / White | spare | ⬜ |
| Knock 1 | B / Grey-ish | Knock sensor | ✅ |
| Knock 2 | B | 2nd knock (if fitted) | ⬜ |

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
| Reverse switch | SB → CAN → ECU | ✅ | ECU sets Gear = 7 (R) on 0x3EB via a PCLink Trigger → cluster shows "R" (cluster remaps 7→−1). RealDash also reads this byte directly (added 2026-09-04) to drive a reverse-camera auto-switch — see `CAN-CONFIG-STATUS.md`. |
| Cruise on/off + set/res ladder | SB → CAN → ECU | ⬜ | resistor ladder on a switchboard analog in |

## Outputs

| XtremeX channel | Loom / wire color | Function (ST185 5S-GTE) | Status |
|---|---|---|---|
| Injection 1–4 | A / Blue family | Injectors, cyl 1–4 (sequential) | ✅ |
| Injection 5–8 | B / Blue family | spare (usable as aux) | ⬜ |
| Ignition 1–4 | A / Orange family | Coils (COP or wasted-spark) | 🟡 confirm ignition type |
| Ignition 5–8 | B / Orange family | spare (usable as aux) | ⬜ |

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
DI and Aux (2026-09-04) are corrected and match `XTREMEX-IO-TABLE.html`; no longer open items here.
Still open, per `DOCS-CLEANUP-PLAN.md`: (1) trigger type/pattern, (2) ignition type (COP vs
distributor/wasted), (3) injector size/impedance, (4) which analog volts carry which
pressure/flex/wideband (An Volt map disagrees with the HTML source on 8/11 channels), (5) idle
valve type — likely moot now under DBW, confirm. Fill each row as it's confirmed, then lock the table.
