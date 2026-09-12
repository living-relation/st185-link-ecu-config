# XtremeX I/O verification — 2026-09-11

Pin numbers, drive types, and pull-ups for the ST185 Link G4X XtremeX harness, checked against official Link documentation. After this pass the live wiring docs agree and are marked confirmed.

## Official sources used

| Source | What it settles |
|---|---|
| [G4X XtremeX Quick Start Guide](https://linkecu.com/documentation/XtremeXQuickstartGuide.pdf) (InDesign 18.3, 2023-06-22) | A/B Superseal pin map (wire-side / ECU-header view), factory loom colours, Temp 1/2 selectable pull-ups, Temp 3/4 fixed 1 kΩ, Aux 1–4 low-side flywheeled, Aux 5–8 high/low + stepper, Aux 9/10 E-throttle or GP, DI 9/10 = CAN 2 or DI, B14 empty, no +5 V on loom B, V-Ethrottle on B5 |
| [G4X XtremeX product page](https://dealers.linkecu.com/G4X-XtremeX) | High-Z injectors only (no peak-and-hold), 8/10 DI @ 10 kHz, configurable pull-ups on AN Temp 1 & 2, Aux 5–8 high/low, onboard baro + IMU |
| PCLink-family Wiring and Installation Manual (G4+ HTML help that the QSG defers to) | Aux 2 A low-side; Aux 5–8 high-side stepper 0.5 A; Aux 9/10 push-pull 4 A; ign high 20 mA @ 5 V; ign/inj as aux = 2 A, **not** flywheeled; An Volt has no pull-up; DI pull-up is a PCLink setting |
| TE Superseal 1.0 | Housing ~15 A; terminals 3-1447221-4 (0.5 mm²) and 3-1447221-3 (0.75–1.25 mm²). ECU pin current is the limit, not the terminal |

The QSG PDF is vendor copyright. It is not stored in this repo. Download it from the Link URL above when re-checking.

## Pin map — every assigned cavity matches the QSG

View: looking into the wire side of the loom (same as looking into the ECU header). Superseal 34-way is 9-8-8-9.

### Connector A

| Pin | QSG function | This build |
|---|---|---|
| A1–A4 | Inj 4, 3, 2, 1 | Inj 4–1 (1400 cc hi-Z) |
| A5 | +14 V | ECU power (via EFI main relay) |
| A6 | +8 V | Cam Hall supply |
| A7 | Shield/Gnd | Shield drain, ECU end only |
| A8 | Trig 1 | Crank VR 36-2 |
| A9 | Trig 2 | Cam Hall |
| A10–A13 | Ign 4, 3, 2, 1 | 1ZZ COP 4–1 (5 V / 20 mA logic) |
| A14 | An Volt 4 | APS main |
| A15 | Temp 1 | ECT (selectable pull-up → 1 kΩ internal) |
| A16 | Temp 2 | Manifold IAT (same) |
| A17 | An Volt 1 | MAP |
| A18–A21 | Aux 4, 3, 2, 1 | AC kill, FP relay, ETB relay, boost (low-side 2 A) |
| A22 | An Volt 2 | TPS main |
| A23 | DI 3 | WSS FL (via NCV1124) |
| A24 | Gnd Out | Sensor ground |
| A25 | Ground | ECU ground |
| A26–A29 | Aux 8, 7, 6, 5 | Start relay, MRS SPD, EFI hold, rad fan |
| A30 | DI 1 | Turbo speed |
| A31 | DI 2 | Flex (ethanol + fuel temp) |
| A32 | +5 V | Sensor 5 V (jumper to loom B) |
| A33 | An Volt 3 | TPS sub |
| A34 | Ground | ECU ground |

### Connector B

| Pin | QSG function | This build |
|---|---|---|
| B1–B4 | Inj 8–5 | Spare low-side aux |
| B5 | V Ethrottle | H-bridge 12 V in (from Aux 2 relay) |
| B6 | Temp 3 | Oil temp (fixed 1 kΩ) |
| B7 | Temp 4 | Charge-pipe IAT (fixed 1 kΩ) |
| B8 | Knock 2 | Spare |
| B9 | Knock 1 | Knock |
| B10–B12 | Ign 8–6 | Spare (Ign 6 is **not** an oil lamp) |
| B13 | Ign 5 | Condenser fan relay (low-side aux, no flywheel — use a relay) |
| **B14** | **empty** | **No terminal** |
| B15 | An Volt 6 | Oil pressure |
| B16 | An Volt 7 | Fuel pressure |
| B17 | Shield/Gnd | Shield drain |
| B18 | Aux 9 (ETB +) | Bosch ETB motor + |
| B19–B21 | DI 6, 5, 4 | WSS RR, RL, FR |
| B22 | Gnd Out | Sensor ground |
| B23 | An Volt 8 | Coolant pressure |
| B24 | An Volt 9 | Fuel level (external divider — An Volt has no pull-up) |
| B25 | Ground | ECU ground |
| B26 | Aux 10 (ETB −) | Bosch ETB motor − |
| B27 / B28 | DI 10 / CAN2 H, DI 9 / CAN2 L | Spare (CAN 2 unused) |
| B29 | DI 8 | Spare / OEM VSS candidate (clutch is on the switchboard) |
| B30 | DI 7 | Start request |
| B31 / B32 | An Volt 10 / 11 | Spare |
| B33 | An Volt 5 | APS sub |
| B34 | Ground | ECU ground |

Comms 6-pin (CAN 1): C1 Brown GND, C2 Blue unused, C3 White CAN H, C4 Green CAN L, C5 Yellow RS232 TX, C6 Grey RS232 RX — same as the G4 communications-port table.

## Capabilities vs this assignment

| Assignment | QSG / manual | Result |
|---|---|---|
| VR crank on Trig 1, Hall cam on Trig 2 | Reluctor / Hall both legal | OK. Cam needs 1.8 kΩ to +8 V |
| 1ZZ COP on Ign 1–4 | Ign high 20 mA @ 5 V | OK for built-in igniter coils |
| 1400 cc hi-Z inj on Inj 1–4 | G4X is saturated only | OK. Do not refit the OEM resistor pack as peak-and-hold |
| ETB on Aux 9/10 + B5 | Motor +/− or GP; V Ethrottle is power **in** | OK. Isolate B5 with Aux 2 until 9/10 are configured |
| Boost / relays on Aux 1–4 | Flywheeled low-side 2 A | OK — all are relay/solenoid coils, not fans |
| Fans / starter / pump via relays | Load must be > 7 Ω or use a relay | OK |
| Ign 5 as condenser-fan aux | Ign as aux is 2 A, **not** flywheeled | OK **only through a relay** (already drawn) |
| MRS on Aux 7 Speedo Out | Aux 5–8 GP PWM / speedo | Channel OK. High level must be scoped (C21) before adding a 5 V pull-up |
| Flex on DI 2 | DI 1–4 = frequency / switch / VVT; ethanol is a DI function | OK. DI pull-up ON; no extra 2.4 kΩ unless the edge is weak |
| WSS on DI 3–6 via NCV1124 | DI is 0–5 V frequency, not a differential VR input | Conditioner required. Threshold note in `docs/devices/VR-WHEEL-SPEED-CONDITIONER.md` still stands |
| Switches on switchboard | DI budget is for frequency | OK. Clutch is **not** on DI 8 |
| Fuel level on An Volt 9 | 0–5 V, no pull-up | External divider required; resistor value still TBD |
| Dual IAT on Temp 2 + Temp 4 | Temp 4 is fixed 1 kΩ | Separate PCLink cal tables required |

## Docs that disagreed (fixed this pass)

| File | Error | Fix |
|---|---|---|
| `XTREMEX-IO-TABLE.html` | Banner said pins UNVERIFIED; “no external pull-ups”; Aux 5–10 lumped as high/low; pin budget counted Ign 6 and DI 8 as used | Confirmed banner; honest pull-up list; Aux 9/10 = ETB push-pull; budget 7 DI + 5 ign |
| `SCHEMATIC-WIRING.html` | **B14 labelled An Volt 6** (QSG: empty). Shield listed as B16 (that is An Volt 7). Clutch drawn to DI 8 | An Volt 6/7 = B15/B16; shield A7/B17; DI 8 spare; clutch on switchboard note |
| `apps/harness-schematic/` | DI 8 = clutch; Ign 6 = oil lamp; README called A6 spare | Clutch → band 3 CSB3; Ign 6 spare; A6 is cam Hall |
| `tune/engine_constants.yaml` | Flex “2.4 k pull-up on signal” | PCLink DI pull-up ON |

## Still open (not pin-map)

- **C18** — which two physical CAN ends get the 120 Ω resistors (install measurement).
- **C21** — Aux 7 MRS high-level voltage on this ECU (scope before a 5 V pull-up).
- **ECU Hold Power** — Aux 6 is the relay, but PCLink also wants an Ignition Switch input. No DI assigned yet; spare DI 8/9/10 or a switchboard VDI.
- Fuel-level divider value and V→% table.
- Band 3 CSB3 I/O connector (clutch, brake, reverse, cruise, cabin temp) still unwired.
- Cluster GPIO in `WIRING.md` is a different domain (ESP32), not re-litigated here.

## Confirmed documents

Once the pin errors above were fixed, these agree with the official QSG and with each other:

- `XTREMEX-IO-TABLE.html`
- `SCHEMATIC-WIRING.html`
- `apps/harness-schematic/index.html` + `README.md`
- `WIRING.md` (CAN topology only; ECU cavities point here)
