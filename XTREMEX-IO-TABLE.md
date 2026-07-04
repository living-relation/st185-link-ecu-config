<!-- STATUS: DRAFT baseline for one-by-one verification. Source: Link G4X XtremeX Quick Start Guide (Installer I/O Table + A/B loom pin diagram). Engine: 1993 Celica GT-Four ST185, 3S-GTE turbo. Date: 2026-07-01 -->
# Link G4X XtremeX — I/O Assignment Table (ST185 3S-GTE)

This is the master pin/channel plan for the **XtremeX** wire-in ECU. It keys off the XtremeX
Quick Start Guide "Installer I/O Table" and the A/B loom diagram (channel name + loom + wire color —
Link assigns functions to these **named channels** in PCLink, not to bare pin numbers).

**Status key:** ✅ assigned (already in CAN/wiring docs) · 🟡 proposed (typical 3S-GTE — confirm) · ⬜ TBD (verify one-by-one)

---

## CAN plan (important)
- **User CAN 1 = the 6-pin Comms/Tuning port** (CAN **H = white**, CAN **L = green**). **All peripheral CAN devices live here**, 1 Mbit/s: center cluster, ECUMaster switchboard, RealDash (listen-only), and the **external lambda controller**.
- **CAN 2 (optional, shares DI 9 / DI 10 on B loom) — left UNUSED.** This keeps DI 9/10 free as digital inputs and puts everything on one bus, as requested.

| CAN device | Frames | Dir |
|---|---|---|
| Center cluster (ESP32-P4) | 0x3E8–0x3EB, 0x3EE (from ECU); 0x3EC/0x3ED (to ECU) | both |
| RealDash (Pi) | 0x3EF, 0x3F0, 0x3F1 | listen-only |
| ECUMaster switchboard | 0x640–0x642 (to ECU); 0x643 (from ECU) | both |
| **External lambda controller** | TBD (controller-specific — see questions) | to ECU |

---

## Inputs

| XtremeX channel | Loom / wire color | Function (ST185 3S-GTE) | Status |
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
| DI 1 | A / Red | Flex-fuel sensor (frequency) → ethanol % + fuel temp | 🟡 confirm |
| DI 2 | A / Red-White | Clutch switch | 🟡 |
| DI 3 | A / Red-Blue | Brake switch | 🟡 |
| DI 4 | B / Grey-Purple | Launch / spare | ⬜ |
| DI 5 | B / Grey-White | spare | ⬜ |
| DI 6 | B / Grey | spare | ⬜ |
| DI 7 | B / Grey-Yellow | spare | ⬜ |
| DI 8 | B / Grey-Green | spare | ⬜ |
| DI 9 / CAN2 L | A / White | **DI only** (CAN2 unused) — spare DI | ⬜ |
| DI 10 / CAN2 H | B / White | **DI only** (CAN2 unused) — spare DI | ⬜ |

## Outputs

| XtremeX channel | Loom / wire color | Function (ST185 3S-GTE) | Status |
|---|---|---|---|
| Injection 1–4 | A / Blue family | Injectors, cyl 1–4 (sequential) | ✅ |
| Injection 5–8 | B / Blue family | spare (usable as aux) | ⬜ |
| Ignition 1–4 | A / Orange family | Coils (COP or wasted-spark) | 🟡 confirm ignition type |
| Ignition 5–8 | B / Orange family | spare (usable as aux) | ⬜ |
| Aux 1 | A / Orange-Yellow | Boost control solenoid | 🟡 |
| Aux 2 | A / Orange-Green | Idle (ISC) — pin of a pair if 3-wire | 🟡 |
| Aux 3 | A / Orange-Blue | Idle (ISC) 2nd / spare | ⬜ |
| Aux 4 | A / Orange-Purple | Fuel pump relay | 🟡 |
| Aux 5 | A / (A-loom) | Radiator fan | 🟡 |
| Aux 6 | A / (A-loom) | AC clutch (or via switchboard low-side) | ⬜ |
| Aux 7 | A / Brown-Orange | Tacho out / CEL | ⬜ |
| Aux 8 | A / Brown-Red | spare | ⬜ |
| Aux 9 (E-throttle +) | A / Purple | **Unused** (ST185 is cable throttle) | 🟡 confirm cable vs DBW |
| Aux 10 (E-throttle −) | A / Purple-White | **Unused** (cable throttle) | 🟡 |

## Power / ground
| Channel | Loom / color | Use |
|---|---|---|
| +5V Out | A / Red | TPS + MAP sensor power |
| +8V Out | A / (A-loom) | 8V sensor power (if used) |
| 14V + | A / (A-loom) | Main ECU battery feed (switched) |
| Ground / Shield-Gnd / Gnd Out | A & B / Black | Sensor grounds, shields |

---

## To finish this table (one-by-one pass)
Confirm, in order: (1) trigger type/pattern, (2) ignition type (COP vs distributor/wasted), (3) injector
size/impedance, (4) which analog volts carry which pressure/flex/wideband, (5) idle valve type, (6) each
Aux output's load, (7) each DI's switch. I'll fill each row as you confirm it, then lock the table.
