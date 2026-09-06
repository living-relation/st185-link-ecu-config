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
| `tables/lambda_target.csv` | Target lambda vs load. Still applies — the external CAN-Lambda controller fills Lambda 1; the target table is ECU-side. |
| `tables/boost_target_psi.csv` | **Street seed** open-loop boost target vs RPM/TPS, caps at 18 psi. Use this one for shakedown. |
| `tables/boost_target_full_psi.csv` | **Full-power** boost target vs RPM, EFR 7163-G / E85, peaks at 30 psi. **Do not load for a first start.** |
| `tables/boost_target_full_detail.csv` | The same full-power curve with estimated flow, compressor efficiency, charge temp and WHP per point. |
| `tables/boost_duty_base_pct.csv` | Boost-control **wastegate duty** base table, open-loop starting values. MAC 4-port + Turbosmart GenV IWG 14 psi spring. |
| `tables/boost_shakedown_stages.csv` | **Staged shakedown** boost/duty tables, Stage 0-3. Load one stage at a time; set the overboost cut for that stage before the first pull. |
| `tables/multi_fuel_blend.csv` | Ethanol % vs fuel/ignition trim multiplier — the blend axis `ve_e85_pct.csv` pairs with. |
| `limits.yaml` | ECU protection limits + cluster cosmetic thresholds. Intentionally loose for the startup map. |
| `docs/` | Engine-side guides: spec, trigger/COP, driveability, limits, first-start, protection, research. |
| `scripts/` | `calc_engine.py`, `build_limits_tracker.py` (generates `docs/LIMITS_PROTECTION_TRACKER.xlsx`). |

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
was **excluded**: it contradicts `XTREMEX-IO-TABLE.html` on roughly ten channels and declares an
onboard `wideband_onboard_lsu49` block, which is a FuryX-only feature. This build uses an external
Link CAN-Lambda on `0x3B6` (conflict C19).

## Status and caveats

**These tables are seeds, not dyno data.** Carried forward verbatim from the source repo's own
note: *"These are conservative placeholders, not dyno data."* Units and axes must match your
PCLink template after loading the Link startup map.

**Two boost target tables, and they are not interchangeable.** `boost_target_psi.csv` is the
street seed (TPS x RPM axes, 18 psi ceiling, matches `targets.boost_psi_street_seed`).
`boost_target_full_psi.csv` is the eventual full-power curve (RPM axis only, 30 psi peak, matches
`targets.boost_psi_max_eventual`) and its own header says *"do NOT load this for a first start"*.
Different axis structures, so they are not drop-in replacements for each other. Ramp:
`boost_shakedown_stages.csv` -> street seed -> full.

**No data above 7000 RPM.** The tables stop at 7000 RPM but `targets.rev_limit_rpm` is 8000, and
`targets.rev_limit_soft_first_start` is 4000. Between 7000 and 8000 RPM PCLink extrapolates off
the last column. Resolve this before any high-RPM running.

**Not imported from the source repo**, as FuryX-specific or repo-meta: `io_assignments.yaml`,
`docs/references/` (FuryX quickstart PDF, dealer HTML, quickstart notes), the I/O docs
(`SENSOR_WIRING.md`, `IO_BUDGET.md`, `PWM_OUTPUTS.md`), the agent/session handoff docs, and
`package_ecu.ps1` (a zip packager for the old standalone repo). `XTREMEX-IO-TABLE.html` is
authoritative for all channel assignment.

**Channel references were corrected on import.** `docs/ENGINE_SPEC.md` carried FuryX assignments
inline — flex fuel moved DI5 → DI2 (C13), reverse moved DI10 → switchboard/CAN (C16), and the
boost/fan/fuel-pump/ethanol Aux numbers were replaced with pointers to `XTREMEX-IO-TABLE.html`
rather than asserting XtremeX channels that are not yet confirmed. `docs/RESEARCH.md` retains its
FuryX evaluation section, marked superseded.

Save the tuned result as a `.pclx` — do not edit these seeds in place once tuning starts.
