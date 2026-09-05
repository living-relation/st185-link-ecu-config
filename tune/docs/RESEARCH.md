# Research notes — ST185 5SGTE hybrid

Private tune-project research. Not dyno data — conservative starting points with citations where available.

## Engine platform

| Topic | Notes |
|-------|-------|
| Hybrid | 5SFE block + forged internals, Gen2 3SGTE head, MLS gasket, 8.5:1 CR |
| Displacement | 2189 cc — Wiseco 87.5 mm, -14 cc dish |
| Oil | 10W-50 high-zinc, Moroso pan, external cooler, 6 mm total relief shim on 15100-74030 pump |
| Bearings | Loose blueprint (~2.5 mil mains, ~2–2.15 mil rods) — oil film matters more when hot/thin |

## Turbo — EFR 7163

- BorgWarner EFR 7163-G, 0.80 A/R twin-scroll, internal WG + speed sensor.
- Street base map targets **12–18 psi**; ECU protection + red overlay at **29 psi** (`config/limits.yaml`).
- Dyno goal ≤30 psi / ~600 bhp documented separately — do not use as first-start boost target.

## Link G4X FuryX (SUPERSEDED — ECU is an XtremeX)

- [FuryX dealer spec](https://dealers.linkecu.com/G4X-FuryX) — 10 DI with CAN2 disabled; onboard LSU; peak-and-hold injectors.
  > **Superseded 2026-07-04.** The ECU is a Link G4X **XtremeX**, which has **no onboard lambda
  > controller** — this build uses an external Link CAN-Lambda on `0x3B6`. See `DOCS-CLEANUP-PLAN.md`
  > conflicts C2 and C19. The 10-DI / CAN2-disabled point still holds. Retained as a record of the
  > original ECU evaluation.
- [Link startup maps](https://linkecu.com/getting-started/start-up-maps/) — start from conservative template, then apply this project's limits.
- [G4X forum](https://forums.linkecu.com/forum/32-g4x/) — trigger polarity, multi-fuel, E-throttle.

## Trigger — 36-2 Toyota 3SGTE pattern

Confirmed for this build:

- **Trigger Mode:** Multitooth / Missing  
- **Trig 1:** 36 teeth, 2 missing, position **Crank**, VR sensor  
- **Trig 2:** **Cam Pulse 1×**, Hall on intake cam  

Verify VR **polarity** on Trigger Scope — incorrect polarity causes high-RPM breakup. See `TRIGGER_COP_SETUP.md`.

## Cams — HKS 264°

| Cam | P/N | Typical lobe center |
|-----|-----|---------------------|
| Intake | 2202-RT063 | **110° ATDC** |
| Exhaust | 2202-RT064 | **103° BTDC** |

272° profiles often use 110° intake / 108° exhaust. Some tuners advance exhaust toward 272° LC for ~13° overlap to help spool — optional experiment; log AFR/EGT/knock if tried.

Install: gears set **slightly retarded** vs factory marks (document final ° in `ENGINE_SPEC.md`).

## Injectors — ATS 1400 cc

- Peak-and-hold on FuryX — configure per ATS sheet.
- Dead time table: `config/tables/injector_dead_time_ms.csv` (ΔkPa vs battery voltage).
- Confirm **Chase Bays rail pressure** so ΔkPa axis matches PCLink.

## Multi-fuel (93 / E85 / blend)

- Continental flex sensor on DI — PWM frequency = ethanol %, pulse width = fuel temp; **2.4 kΩ pull-up** on signal (open-collector output).
- Chase Bays FPR: **43.5 psi (3 bar) base**, **1:1 boost-referenced**, return system — starting point for startup map; confirm on gauge at key-on.
- Modelled Multi-Fuel in PCLink; E85 needs ~35–40% more fuel vs stoich on 93.
- Blend table seed: `config/tables/multi_fuel_blend.csv`.

## Oil pressure — hot idle research

### Toyota factory (3SGTE BGB, cited on MR2 forums)

| Condition | Minimum |
|-----------|---------|
| Hot idle | **4.3 PSI** |
| 3000 RPM | **36 PSI** |

Sources: [MR2OC oil pressure thread](https://www.mr2oc.com/threads/oil-pressure-reading-on-3sgte.61103/) (owners cite BGB values).

### Real-world healthy 3SGTE (warm idle)

Forum reports cluster around **15–25 PSI** at warm idle (900–1100 RPM), higher when cold. Gen3 owners commonly see ~20 PSI warm.

### This build (loose clearances + 10W-50 + cooler)

- Expect **lower hot-idle PSI than a tight OEM-clearance motor** — not necessarily a fault if stable and rises with RPM.
- **v1 base map:** use **loose** oil limit from `limits.yaml` (5 PSI + high RPM/MAP gates) — do not tighten until engine runs and hot-idle is logged.
- **After stable running / dyno:** measure and apply `oil_press.*_tuned_ref` in a new `.pclx`.
- **Procedure (tuned map, not first start):**
  1. Warm up 20+ min; oil temp ≥180°F.
  2. Log idle PSI at 900–1100 RPM (A/C off).
  3. Set Link **limit** (no warning tier) with RPM/MAP gating so hot idle never false-cuts.
  4. Under load, factory 36 PSI @ 3000 RPM is a sanity reference.

Problem example: hot idle **7 PSI** with long turbo feed lines reported on MR2 board — investigate restriction/leaks before lowering limits to match.

### Cluster vs ECU

- Left ring `DASH_OIL_PRESS_MIN` (25 PSI @ 2000 RPM) is **cosmetic** until hot-idle is logged — may flash falsely on loose-clearance warm idle.
- Low oil pressure: Link **limit** only (no warning tier). Cluster arc color from PSI. If limit cuts engine → **FUEL CUT** / **IGN CUT** on red box — **not** “oil pressure low” text or CAN byte.
- Coolant pressure: ECU limit/logging only if configured — not red-box alarm.

## References in repo

- ~~`docs/references/FuryXQuickstartGuide.pdf`~~ — FuryX-specific, not imported (ECU is an XtremeX)
- `docs/references/linkecu-furyx-dealer.html`
- Center cluster CAN: `config/can/link_g4x_can_setup.*`
