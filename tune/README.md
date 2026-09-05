# Engine calibration data (`tune/`)

PCLink table seeds and machine-readable engine constants for the ST185 5S-GTE build.

This directory covers **engine calibration only**. It is not an I/O or wiring source — see
`XTREMEX-IO-TABLE.html`, which is authoritative for channel assignment per `DOCS-CLEANUP-PLAN.md` §7.

## Files

| File | Purpose |
|---|---|
| `engine_constants.yaml` | Machine-readable engine/vehicle constants — bore, stroke, cams, trigger, injectors, turbo, fuel, targets. |
| `tables/ve_base_pct.csv` | Main VE vs RPM and MAP (kPa) — 93 octane seed. |
| `tables/ve_e85_pct.csv` | E85 overlay — ~8% richer than the 93 seed at the same cells. |
| `tables/ignition_base_deg.csv` | Ignition advance [° BTDC] — retarded under boost. |
| `tables/injector_dead_time_ms.csv` | ATS 1400 cc dead time vs ΔkPa and battery voltage. |

All three main tables share one axis pair: **MAP 20–200 kPa (rows) × RPM 800–7000 (columns)**.

## Provenance

Imported 2026-09-04 from `st185-furyx-base-map` (commit `8be9a0b`), a **Link G4X FuryX**-era repo.
The engine data was verified accurate and carried over unchanged. Three ECU-specific fields in
`engine_constants.yaml` were corrected on import:

| Field | Was (FuryX) | Now (XtremeX) | Reason |
|---|---|---|---|
| `ecu.model` | `Link G4X FuryX` | `Link G4X XtremeX` | `DOCS-CLEANUP-PLAN.md` conflict C2 |
| `driveline.reverse_switch` | `DI10` | switchboard → CAN → ECU | Conflict C16; DI 9/10 are spare, CAN2 unused |
| `injectors.dead_time_table` | `config/tables/…` | `tune/tables/…` | Path follows the file |

Nothing else from the base-map repo was imported. In particular its `config/io_assignments.yaml`
was **excluded**: it contradicts `XTREMEX-IO-TABLE.md` on roughly ten channels and declares an
onboard `wideband_onboard_lsu49` block, which is a FuryX-only feature. This build uses an external
Link CAN-Lambda on `0x3B6` (conflict C19).

## Status and caveats

**These tables are seeds, not dyno data.** Carried forward verbatim from the source repo's own
note: *"These are conservative placeholders, not dyno data."* Units and axes must match your
PCLink template after loading the Link startup map.

**No data above 7000 RPM.** The tables stop at 7000 RPM but `targets.rev_limit_rpm` is 8000, and
`targets.rev_limit_soft_first_start` is 4000. Between 7000 and 8000 RPM PCLink extrapolates off
the last column. Resolve this before any high-RPM running.

**Companion tables not imported.** `ve_e85_pct.csv` is designed to be used with a Modelled
Multi-Fuel blend axis, whose `multi_fuel_blend.csv` was not brought across. `lambda_target.csv`
and `boost_target_psi.csv` also exist in the source repo and are available if wanted.

Save the tuned result as a `.pclx` — do not edit these seeds in place once tuning starts.
