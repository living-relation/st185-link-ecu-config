# Engine spec

## Confirmed

| Item | Value |
|------|-------|
| Displacement | 2189 cc (87.5 × 91 mm) |
| CR | 8.5:1 |
| Block / head | 5SFE block, Gen2 3SGTE head, MLS gasket |
| Cams | HKS 264° IN 2202-RT063 / EX 2202-RT064 |
| Cam LC baseline | 110° ATDC intake, 103° BTDC exhaust (gears slightly retarded — log final ° at install) |
| Crank trigger | **36-2** multitooth/missing, VR, position = Crank |
| Cam sync | Cherry Hall, Cam Pulse 1× |
| Injectors | ATS 1400 cc top-feed, **high impedance (saturated)**, flow-matched. PCLink injector drive = **Saturated**, not Peak & Hold. Stock resistor pack deleted. |
| Injector dead time | `tune/tables/injector_dead_time_ms.csv` |
| Coils | Toyota 1ZZ COP ×4 sequential |
| Turbo | BorgWarner EFR 7163-G, 0.80 A/R, internal WG |
| WG actuator | Turbosmart **TS-0620-4012** GenV IWG, **14 psi** spring |
| Boost control | MAC 3-port solenoid — Aux 1 (see `XTREMEX-IO-TABLE.html`) |
| FMIC | Bar-plate **4 × 14 × 28 in**, **3 in** in/out |
| Fuel pump | Walbro F90000295, full-on via SSR — channel per `XTREMEX-IO-TABLE.html` |
| FPR | Chase Bays, **43.5 psi (3 bar) base**, **1:1 boost-referenced**, return system, 8AN rail |
| Flex fuel | Continental-style PWM sensor (AEM/Innovate rebrand OK), DI2, **2.4 kΩ pull-up** on signal |
| Oil | 10W-50 high-zinc, pump 15100-74030, **6 mm** total relief shim, external cooler, Moroso pan |
| Bearings | ~2.5 mil mains, ~2.0–2.15 mil rods (ATS blueprint) |
| Transmission | Toyota **E150F**, OEM VSS, reverse via ECUMaster switchboard → CAN → ECU (Gear=7 on 0x3EB) |
| Driveline | ST185 AWD — viscous center coupling; rear **RX300 Torsen LSD** |
| Fans | Slimline 12 V **12 in** pusher ×2 (P/N not critical), PWM via SSR — channel per `XTREMEX-IO-TABLE.html` |
| ETB | Bosch 74 mm + Subaru electronic pedal |
| ECU | Link G4X XtremeX, CAN1 dashboard @ 1 Mbit/s, CAN2 disabled → 10 DI |
| Rev limit (config) | 8000 RPM eventual; use **4000** GP soft limit for first idle |
| Aux (spare) | Reserved for auxiliary ethanol injection later — **not used** on startup map; channel per `XTREMEX-IO-TABLE.html` |

Machine-readable: `config/engine_constants.yaml`

## Before first crank (harness / PCLink)

- [ ] **Final cam gear degrees** from marks (intake + exhaust)
- [ ] **Cherry Hall sensor P/N** and gap
- [ ] **Continental flex P/N** on harness label
- [ ] **Trigger Scope** — 36-2 pattern and VR polarity
- [ ] **E150F VSS** pulses/mile — calibrate road speed in PCLink after first drive
- [ ] **Reverse** via switchboard → CAN, verified on cluster gear display
- [ ] **MAC 3-port** plumbing to EFR IWG verified

## Optional / later (not startup map)

- [ ] Cruise stalk ladder on AN9 — ST185 EWD p116–121: Cancel ~413 Ω, Resume ~68 Ω, Set ~198 Ω (pins 5–17)
- [ ] Coolant pressure limit kPa in PCLink
- [ ] Hot-idle oil PSI log @ oil temp ≥180°F (for a future tuned map — v1 limit stays loose)
- [ ] Ethanol injection vs IC spray decision (spare Aux)
- [ ] Exhaust cam advance toward 272° LC experiment
