# ST185 wiring audit — 2026-09-18

## Purpose
Read-only pass: living ECU IO vs harness.design vs HTML/MD faces. **No mass rewrites this pass.**

Vehicle: **1993** ST185 / 5S-GTE / Link G4X XtremeX.

## Trust order (Seeker's lamps)
1. Latest Claude/Cursor wiring decisions
2. `harness.design` — mechanical loom SoT
3. `XTREMEX-IO-TABLE.html` — ECU IO / colour SoT

Do not circular-reconcile HTML↔MD.

## Bottom line
Living ECU IO channel IDs match pin-for-pin across `XTREMEX-IO-TABLE.html` + repo `docs/harness/*.harness`. No material channel mismatches.

## Conflict table

| Priority | Item | Note |
|----------|------|------|
| HIGH | `bh_c` | **LOCKED delete** — Pass A: remove bh_c_*; migrate HV EngineRoom/RADLOK pass-thru |
| MED | B27/B28 | Frozen VERIFY says Spare; living SoT is B28 = DI9 Ign Switch — leave VERIFY frozen |
| MED | A7 shield | **LOCKED Green/Yellow** to match XTREMEX-IO-TABLE |
| LOW | Gnd Out colour | Black vs Black/White; OneDrive monolith missing B28 (mirror, not ACTIVE) |
| INFO | BOARD-VERIFY | "pins unverified" is a stale snapshot |

## Draft (not committed)
`C:\Users\danie\AppData\Local\Temp\st185-audit\ecu_pin_graph_DRAFT.csv`

## Update plan (after Daniel okays)
1. Crown pin-graph CSV under `docs/harness/`
2. Pass A — migrate/delete `bh_c`
3. Colour hygiene A7 / Gnd Out
4. Regenerate BUILD-LIST / NEED-TO-BUY / schematic faces from crown
5. Leave VERIFY / AUDIT / BOARD frozen
6. Stop editing OneDrive monolith

## Consolidation
Option A: pin-graph as IO index + four `.harness` as manufacturing SoT; HTML/MD generated or thin pointers. Keep harness.design first-class.

## Locked decisions (Daniel via Grimoire 2026-09-18) — ALL sealed; Pass A unjarred
Living SoT + Link primary + Daniel locks:
- **CAN 2 unused** — DI9/DI10 free as ordinary DIs; all buses on **CAN 1**
- **Hold Power required** for ETB key-off — Aux 6 (A28) + DI 9 (B28)
- **V-Ethrottle (B5)** = **12V power IN** via Aux 2 (A20) relay — not ECU out
- **+8V cam Hall:** A6 +8V Out + **1.8k** pull-up (not kit 2.4k/12V)
- **AC-kill-only / no Request DI** — intentional OEM amp; polarity **ground = kill, float = run**
- **Pin-graph CSV** — commit **after** Pass A
- **Loom C / bh_c** — **delete** `bh_c_*`; no bulkhead; pass-thru fenders / outside bay; migrate HV into EngineRoom / RADLOK
- **A7 colours** — **Green/Yellow** to match XTREMEX-IO-TABLE shield group (not sacred Gray)
- **B29** — **VSS from trans for mph** (keep reserved / wire it)
- **Fuel level** — OEM sender + **voltage divider** (approach locked; resistor value TBD for BOM if unset)
- **Git** — **feature branch only**; no main until verified

## Open locks (Daniel)
None — Pass A **IN PROGRESS** (Daniel Go 2026-09-18). Writer: **Grimoire only**, local DansPC, feature branch. Cloud Agent jarred (usage). No dual-cast (Claude/Cursor off these files). No main until verified. Fuel-divider ohms jarred for BOM. Branch name pending first commit.
## Related shelves
- `docs/BOARD-VERIFY-2026-09-11.md`
- `docs/HARNESS-FACES-2026-09-11.md`
- `XTREMEX-IO-TABLE.html`
## Sixth crown (2026-09-18)
Link G4X XtremeX QSG + Link admin posts (ST185/MR2) + HP Academy / official manuals — verify living IO before Pass A. 3SGTE AC threads = pattern evidence only, not ST185 pin fact.

Pass A **unjarred** (2026-09-18). All locks sealed. Checklist: delete bh_c, A7 to Green/Yellow, B29 VSS, fuel divider note, AC kill polarity, regenerate build-list faces. Feature branch only.
## Link-canon match table (2026-09-18)

Primary: XtremeX QSG 2023 (not 2016 G4+), TST185X OEM meanings only, Adamw staff posts. 3SGTE/HPA = AC pattern only.

| Claim | Living SoT | Link primary | Verdict |
|-------|------------|--------------|---------|
| B28 = DI9 Ign Switch | XTREMEX-IO-TABLE: DI9 Ign Switch (Hold Power); CAN 2 unused; Aux 6 EFI hold | QSG: DI9 switch or CAN2; Adamw: Ign DI needed when post-key-off hold | **MATCH cavity** — B28 as DI9 allowed by QSG; Hold Power is **project choice** (Adamw: often skip on DBW). Ink as allowed + intentional, not Link-required. PCB-rev for DI9/CAN2 mux still unproven |
| B27 = DI10 Available | CAN 2 unused | QSG PCB >=1.4 DI9/10 vs CAN2 | **MATCH** if board not using CAN2 — confirm PCB rev once |
| Aux AC / FP / fan | Project Aux + DI | Staff pattern Aux+DI+Basic; TST185X OEM pins are plug-in only | **MATCH pattern** — do not copy TST185X pin numbers onto wire-in |
| Ign colours Violet / shield GY | This harness column | QSG defers to PCLink; no admin override | **KEEP** XTREMEX-IO-TABLE |
| bh_c delete | Consolidation plan | No Link post | **Project decision** — still Daniel lock #1 |
| Frozen VERIFY B28 Spare | Dated record | Living + QSG allow DI9 switch | **Leave frozen** — not a living conflict |

**Bottom line:** Link-canon does not force a pin rewrite. B28 DI9 Ign Switch = allowed + intentional (Hold Power project choice, not Link-required). PCB-rev for DI9/CAN2 mux unproven. Pass A **unjarred**. All locks sealed (bh_c delete, A7 GY, B29 VSS, fuel divider approach, AC kill polarity, Hold Power, CAN2, B5, +8V, pin-graph after Pass A). Feature branch only.
## Forum dive topics (Daniel 2026-09-18)
Also check Link forum discussions on:
- Electronic throttle body
- Electric throttle pedal
- AC control via OEM AC amplifier (Link only sends AC kill to the amplifier)
- ECU power hold wiring
## Forum dive staff brief (2026-09-18)
- **ETB + pedal:** Adamw — Aux9/10 motor; TPS/APS dual AN Volts; +5V + sensor gnd. Matches living Aux9/10 + B5. No pin rewrite.
- **Power hold:** Ign Switch DI mainly stepper keep-alive; for DBW key often cuts ECU power. Aux6+DI9 Hold Power = **allowed intentional**, not QSG-required.
- **OEM AC amp kill-only:** Staff Basic wants DI Request + Aux Clutch. Living kill-only to OEM amp = **intentional override** — confirm polarity; do not invent Request DI to match Link.
- **Ignore:** TST185X pin numbers; non-staff pinouts; Hold Power as Link-mandated for DBW.
