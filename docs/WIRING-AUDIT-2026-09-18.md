# ST185 wiring audit — 2026-09-18

## Purpose
Read-only pass: living ECU IO vs harness.design vs HTML/MD faces. **Pass A mechanical applied** on feature branch (see below).

Vehicle: **1993** ST185 / 5S-GTE / Link G4X XtremeX.

## Trust order (Seeker's lamps)
1. Latest Claude/Cursor wiring decisions
2. `harness.design` — mechanical loom SoT
3. `XTREMEX-IO-TABLE.html` — ECU IO / colour SoT

Do not circular-reconcile HTML↔MD.

## Bottom line
Living ECU IO channel IDs match pin-for-pin across `XTREMEX-IO-TABLE.html` + repo `docs/harness/*.harness`. No material channel mismatches.

**Pass A COMPLETE** (2026-09-18, branch `pass-a-bh-c-delete-locks` @ `37af8f6` pushed):
- Commits: `37dab05` residue · `4aa016f` bh_c delete · `0c868d4` B29/fuel/AC IO · `37af8f6` audit + BOM + pin-graph crown
- `bh_c_*` deleted from ACTIVE Signal + Power (empty shells + leftover HV). Fan/EPS HV already live in `ST185-EngineRoom-C.harness` (direct, no HDP20). ETB 12 V via bh_c removed as leftover — V-Ethrottle remains `k_etb` → B5 (`w82`); do not invent A/B cavities.
- A7 shield bulkhead run `w12_c` / `w12_e`: **Gray → Green/Yellow**
- Gnd Out harness colours: **Black → Black/White** (Power `sp_gndout*` rails)
- B29 / DI8: **SEALED car-side** — gearbox **3-wire 12V Toyota VSS** (not 4-wire); mate = **generic oval 3-pin plug with socket contacts**, **PN TBD**; signal → B29 / DI 8; oval cavity map TBD (do not invent); **not** OEM SPD tap (path A). Stub `vss_gbx` in Signal (no wire yet).
- Fuel level: OEM sender + divider locked; **Ω TBD** (470 Ω = starting guess only)
- AC kill: intentional OEM amp; **ground = kill, float = run**
- BUILD-LIST / NEED-TO-BUY regenerated from harness crown

## Conflict table

| Priority | Item | Note |
|----------|------|------|
| DONE | `bh_c` | **Deleted** from Signal + Power ACTIVE. EngineRoom-C / RADLOK remain SoT for HV fans/EPS / heavy DC |
| MED | B27/B28 | Frozen VERIFY says Spare; living SoT is B28 = DI9 Ign Switch — leave VERIFY frozen |
| DONE | A7 shield | **Green/Yellow** on Signal `w12_c`/`w12_e` (matches XTREMEX-IO-TABLE) |
| DONE | Gnd Out colour | Power rails **Black/White** |
| INFO | BOARD-VERIFY | "pins unverified" is a stale snapshot |
| LOCKED | B29 harness wire | **Path B:** gearbox **3-wire 12V Toyota VSS** → generic **oval 3-pin plug (socket contacts)**, part # TBD; signal → **B29 / DI8**. Power/gnd/pin map on oval TBD. Path A (OEM SPD tap) jarred. |
| OPEN | Fuel divider Ω | Approach locked; value TBD for BOM/calibration |

## Pin-graph (crowned on Pass A)
`docs/harness/ecu_pin_graph.csv` (crowned @ `37af8f6`).

## Update plan (after Daniel okays)
1. Crown pin-graph CSV under `docs/harness/` (optional / next)
2. ~~Pass A — migrate/delete `bh_c`~~ **DONE**
3. ~~Colour hygiene A7 / Gnd Out~~ **DONE**
4. ~~Regenerate BUILD-LIST / NEED-TO-BUY~~ **DONE** (this pass)
5. Leave VERIFY / AUDIT / BOARD frozen (BOARD/VERIFY still frozen; this audit is the living Pass A record)
6. Stop editing OneDrive monolith
7. Draw B29→`vss_gbx` signal wire once oval cavity map (which cavity = SIG) is known; set fuel-divider Ω at calibration. PN for oval 3-pin still TBD.

## Consolidation
Option A: pin-graph as IO index + four `.harness` as manufacturing SoT; HTML/MD generated or thin pointers. Keep harness.design first-class.

## Locked decisions (Daniel via Grimoire 2026-09-18) — ALL sealed; Pass A applied
Living SoT + Link primary + Daniel locks:
- **CAN 2 unused** — DI9/DI10 free as ordinary DIs; all buses on **CAN 1**
- **Hold Power required** for ETB key-off — Aux 6 (A28) + DI 9 (B28)
- **V-Ethrottle (B5)** = **12V power IN** via Aux 2 (A20) relay — not ECU out
- **+8V cam Hall:** A6 +8V Out + **1.8k** pull-up (not kit 2.4k/12V)
- **AC-kill-only / no Request DI** — intentional OEM amp; polarity **ground = kill, float = run**
- **Pin-graph CSV** — crowned on Pass A @ 37af8f6
- **Loom C / bh_c** — **deleted** `bh_c_*` from ACTIVE; no bulkhead; EngineRoom-C / RADLOK pass-thru
- **A7 colours** — **Green/Yellow** (applied on Signal shield bulkhead run)
- **B29** — **SEALED**: gearbox **3-wire 12V Toyota VSS** (not 4-wire); generic oval 3-pin socket plug **PN TBD**; signal → B29 / DI 8; cavity map TBD; **not** OEM SPD tap (path A)
- **Fuel level** — OEM sender + **voltage divider** (Ω TBD)
- **Git** — **feature branch only**; no main until verified

## Open locks (Daniel)
None on policy. Remaining **build** openers: oval 3-pin **PN TBD** + which cavity is SIG (do not invent PWR/SIG/GND); fuel-divider Ω for BOM. Branch `pass-a-bh-c-delete-locks` only — **no main merge**. Writer: Grimoire / local DansPC.


## Related shelves
- `docs/BOARD-VERIFY-2026-09-11.md`
- `docs/HARNESS-FACES-2026-09-11.md`
- `XTREMEX-IO-TABLE.html`

## Sixth crown (2026-09-18)
Link G4X XtremeX QSG + Link admin posts (ST185/MR2) + HP Academy / official manuals — verify living IO before Pass A. 3SGTE AC threads = pattern evidence only, not ST185 pin fact.

Pass A **applied** (2026-09-18). Checklist: delete bh_c ✅, A7 to Green/Yellow ✅, B29 VSS (IO) ✅, fuel divider note ✅, AC kill polarity ✅, Gnd Out BW ✅, regenerate build-list faces ✅. Feature branch only.

## Link-canon match table (2026-09-18)

Primary: XtremeX QSG 2023 (not 2016 G4+), TST185X OEM meanings only, Adamw staff posts. 3SGTE/HPA = AC pattern only.

| Claim | Living SoT | Link primary | Verdict |
|-------|------------|--------------|---------|
| B28 = DI9 Ign Switch | XTREMEX-IO-TABLE: DI9 Ign Switch (Hold Power); CAN 2 unused; Aux 6 EFI hold | QSG: DI9 switch or CAN2; Adamw: Ign DI needed when post-key-off hold | **MATCH cavity** — B28 as DI9 allowed by QSG; Hold Power is **project choice** (Adamw: often skip on DBW). Ink as allowed + intentional, not Link-required. PCB-rev for DI9/CAN2 mux still unproven |
| B27 = DI10 Available | CAN 2 unused | QSG PCB >=1.4 DI9/10 vs CAN2 | **MATCH** if board not using CAN2 — confirm PCB rev once |
| Aux AC / FP / fan | Project Aux + DI | Staff pattern Aux+DI+Basic; TST185X OEM pins are plug-in only | **MATCH pattern** — do not copy TST185X pin numbers onto wire-in |
| Ign colours Violet / shield GY | This harness column | QSG defers to PCLink; no admin override | **KEEP** XTREMEX-IO-TABLE |
| bh_c delete | Consolidation plan | No Link post | **Project decision** — applied Pass A |
| Frozen VERIFY B28 Spare | Dated record | Living + QSG allow DI9 switch | **Leave frozen** — not a living conflict |

**Bottom line:** Link-canon does not force a pin rewrite. B28 DI9 Ign Switch = allowed + intentional (Hold Power project choice, not Link-required). PCB-rev for DI9/CAN2 mux unproven. Pass A **complete** on feature branch. Feature branch only — no main until verified.

## Forum dive topics (Daniel 2026-09-18)
Also check Link forum discussions on:
- Electronic throttle body
- Electric throttle pedal
- AC control via OEM AC amplifier (Link only sends AC kill to the amplifier)
- ECU power hold wiring
## Forum dive staff brief (2026-09-18)
- **ETB + pedal:** Adamw — Aux9/10 motor; TPS/APS dual AN Volts; +5V + sensor gnd. Matches living Aux9/10 + B5. No pin rewrite.
- **Power hold:** Ign Switch DI mainly stepper keep-alive; for DBW key often cuts ECU power. Aux6+DI9 Hold Power = **allowed intentional**, not QSG-required.
- **OEM AC amp kill-only:** Staff Basic wants DI Request + Aux Clutch. Living kill-only to OEM amp = **intentional override** — polarity confirmed ground=kill float=run; do not invent Request DI to match Link.
- **Ignore:** TST185X pin numbers; non-staff pinouts; Hold Power as Link-mandated for DBW.

## VSS car-side seal (Daniel 2026-09-18)
- **Sensor:** gearbox **3-wire 12V Toyota VSS** (not 4-wire).
- **Connector:** generic **oval 3-pin plug with socket contacts**; **part number TBD**.
- **ECU landing:** signal → **B29 / DI 8** for mph.
- **Pin map:** oval cavities PWR / SIG / GND = **TBD** — do not invent.
- **Not chosen:** OEM SPD tap (path A).
- **Fuel divider Ω:** remains **TBD** (unchanged).
- Harness: stub connector `vss_gbx` + part `cp_vss_oval3` in `ST185-Signal.harness`; B29 still `notConnected` until SIG cavity known.
