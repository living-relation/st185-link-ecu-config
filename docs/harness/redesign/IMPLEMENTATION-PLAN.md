# Harness Redesign — Implementation Plan

**Date:** 2026-09-27
**Works from:** [`DECISIONS.md`](DECISIONS.md) (frozen decision record: redesign plan + checker audit)
**Baseline:** `main` at `4e782d9`; `python docs/harness/check_all.py` passes on it.

## Status (2026-09-27)

| Phase | State |
|---|---|
| 0 Freeze the record | Done |
| 1 Independent fixes | Done |
| 2 Convention + registry | Done (`interfaces.json`, `model.py`, `INTERFACES.md`) |
| 3 New gates | Done - all HARD |
| 4-5 Rear / front wheel speed | Done (D1 = two-drain 6-way front, D2 = DT 6-way) |
| 6 CSB3, OEM flying leads, A/C coolant switch | Done (22 + 2 flying leads; ambient and pressure-switch circuits stay factory wiring) |
| 7 Inventory restructure | ECU/cabin merge and Rear Fuel done. **Engine re-split by bulkhead letter not done**: 15 devices (injectors, coils, and the oil/fuel/coolant pressure, oil temp, charge-pipe IAT, ETB and VSS sensors) take signal through one bulkhead and rail through the other; splitting needs a rail re-route decision |
| 8 Generators + legacy retirement | Done (owner/interface-aware lists; legacy tools archived) |
| 9 Propagation | Done |

The remaining 9 `cp_xref` dummies are registered references (one harness populating a
cavity another owns); turning any into an inline connector is a per-circuit part choice.

Every phase below ends with `check_all.py` green, one commit per logical change, and a push.
Nothing in `archive/`, `legacy-prebuild/` or a checker script is deleted until the phase that
says so.

---

## 1. Conflicts with current rules — settle before drawing edits

Checking the decision record against the repo found six places where it collides with a rule
that is binding today, or leaves a choice open. Phase 1 needs none of them; Phases 3+ need all
of them.

### D1 — Front wheel-speed drain vs. "A7 and B17 are never joined" (blocking)

`sot/channels.csv` puts front-left on **ECU-A A23** (screen A7) and front-right on
**ECU-B B21** (screen B17). The record says the front output is one 4-core cable with one drain
on pin 5. One drain can only reach one shield ground, so either the FR signal rides a loom-A
screen or A7 and B17 meet through the cable. Today that is avoided on purpose: FR has its own
1-core screened cable to B17, floating at the VRC (`SHIELD-RULES.md` §6.30, CSV row 83).

Rear has no conflict: RL B20 and RR B19 are both loom B → B17.

Options:

| | Change | Cost |
|---|---|---|
| **a** | 6-way front interface: 5V, Gnd, FL, FR, drain-A (main cable screen → A7), drain-B (FR's own screen → B17, floats at VRC). Keeps §6.30 exactly. | Front connector is 6-way, not 5; front cable is 4-core+drain plus a 1-core screened. |
| b | Move FL to a loom-B frequency input (or FR to loom A) so both front signals share one screen. | Needs a free DI on the other ECU connector. The CSV shows no spare DI on either; only An Volt 10/11 are free, and they are not frequency inputs. Would mean moving another channel. |
| c | Accept one screen for both, terminated at A7 or B17. | Breaks an absolute rule. Not recommended. |

**Recommendation: (a).** No ECU pin moves, no SoT change, and the absolute shield rule stands.

### D2 — "5-pin Deutsch" connector part (blocking)

Deutsch DT/DTM/AT come in 2, 3, 4, 6, 8, 12 ways; there is no 5-way DT. Sourcing order is owned
stock → TE → other (`docs/sourcing/README.md`).

| | Part | Notes |
|---|---|---|
| **a** | `DT04-12PA` / `DT06-12SA` + wedgelocks, **2 sets on hand** | Already claimed for the rear trunk inline (plan 6.41). One set per side covers front and rear with no purchase; unused cavities get plugs. Bulky for 5-6 circuits. |
| b | `DT04-6P` / `DT06-6S` + `W6P` / `W6S`, buy | Right-sized; 6th way is the spare (or the D1(a) drain-B). Size-16 contacts are in stock. |
| c | Deutsch HD10 5-way | True 5-way, round, needs its own contacts. |

**Recommendation: (b)** if buying is acceptable, otherwise (a). Either way a 6-way also fits D1(a).
Record the chosen pin map (pin 1 +5V, 2 Gnd Out, 3 L out, 4 R out, 5 drain[, 6 drain-B]) in
`DECISIONS.md` before Phase 4.

### D3 — Harness inventory is incomplete and restructures two looms (blocking for Phase 7)

The record's inventory (ECU/cabin, Engine-A, Engine-B, Loom C, Front WS, Rear WS, Rear Fuel, A/C
spur) leaves out drawings that exist today and changes two:

- **Not listed:** `ST185-CAN`, `ST185-AntiTheft`, `ST185-ClusterLED`, and the cabin accessory
  loom that owns the CSB3 plug (plan 6.41). Assumed kept as-is unless told otherwise.
- **ECU/cabin merges** `ST185-A-ECU` + `ST185-B-ECU` into one drawing.
- **Engine-A / Engine-B by bulkhead letter.** Today `A-*` carries the signal circuits over
  *both* bulkheads and `B-*` the power circuits (`docs/harness/README.md`). The record wants
  Engine-A = everything behind bulkhead A. That moves conductors between engine files.

Confirm the final file list and names before Phase 7.

### D4 — Rear Fuel boundary

Plan 6.41 routed fuel level (B24 + ground) through the same 12-way rear inline as the rear VRC.
The record makes Rear Fuel its own harness, and every crossing needs its own inline connector.
Decide Rear Fuel's cabin-side connector (a DT 2- or 4-way is the obvious fit). The fuel pump
keeps its own connector per 6.41.

### D5 — A/C coolant switch details

Needed before Phase 6: the switch part, which spare **bulkhead A** cavity it crosses on (A is
the signal bulkhead and has size-20 cavities; check free ones with `audit_bh_collisions.py`),
the cabin inline connector part, and the A/C amplifier connector/pin/page from the EWD for the
flying lead. The existing Loom C note already cites EWD p150 (amplifier conn C) and p152.

### D6 — CSB3 A/C inputs also exist as CAN switch bits

Removing cabin temp / evap core / A/C request is a harness change, but the same inputs appear
as CSB3 frame `0x640` switch bits (`bench/frames.py` `SW_EVAP_CORE`, `SW_AC_REQUEST`;
`CAN-BUS-ID-ALLOCATION-TABLE.md` rows 144-145; `ECUMASTER_SWITCHBOARD_SETUP.md`).
`center-cluster-esp32-p4/main` does not decode `0x640`, so the cluster is unaffected. The plan
marks those bits **unassigned** in the docs and leaves the frame layout, `frames.py` constants
and `link_g4x_realdash.xml` alone. That keeps it a docs-only change on the CAN side, reconciled
across Link, RealDash and CSB3 per `RECONCILIATION-RULES.md` Rule 2.

### What the redesign supersedes

Once D1-D4 are settled, record these as superseded in `HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md`
(short pointer, not a rewrite):

- §6.41 "Wheel speed - split front and rear": front VRC and drops live **in loom C**, outputs
  merge into the loom of their ECU pin → front and rear become separate Y harnesses ending at
  their own inline connector; the ECU/cabin harness owns the spurs.
- §6.41 "Rear trunk loom": one 12-way inline for VRC + fuel level → separate Rear WS and Rear
  Fuel harnesses (D4).
- §6.41 "Cabin accessory loom" owning the CSB3 via `cp_xref` cross-references → CSB3 plug is a
  `real_connector`, and other drawings use interface records, not `cp_xref`.
- `SHIELD-RULES.md` §6.30 wording, only if D1 is not (a).

---

## 2. Phases

### Phase 0 — Freeze the record (this PR)

- `docs/harness/redesign/DECISIONS.md` — the frozen record.
- `docs/harness/redesign/IMPLEMENTATION-PLAN.md` — this file.

### Phase 1 — Independent fixes (no decision needed)

One commit each, `check_all.py` after each:

1. **Bulkhead A c32 → `spare (size 20)`.** It is labeled "Trig 2 cam signal (after 1.8k
   pull-up)" on `bh_a_fw` / `bh_a_eng` in A-ECU, A-engine, B-ECU, B-engine and CAN (both
   halves in CAN). No wire lands on it; Trig 2 is ECU A9. Label-only; keep the plug.
2. **Remove CSB3 A/C inputs from the harness.** `ST185-A-ECU` `csb3io` cavities "A1 - Cabin
   Temp", "S1 - Evap Core", "S2 - AC Request" → spare (plug, not contact, per
   `audit_cavity_parts.py`); drop any wires to them and their cavity-note lines.
3. **Docs for D6.** `ECUMASTER_SWITCHBOARD_SETUP.md` (Analog 1 cabin temp, switch bits 1-2,
   the checklist item) and `CAN-BUS-ID-ALLOCATION-TABLE.md` 0x640 switch rows → "unassigned
   (A/C is the OEM amplifier's, 2026-09-27)".
4. **CAN termination.** Mark the plan 6.55 entry settled, per the record. No wiring change.

Regenerate `NEED-TO-BUY.md` / `HARNESS-BUILD-LIST.csv` / `min/` through `check_all.py`.

### Phase 2 — Interface and ownership convention

Write `docs/harness/redesign/INTERFACES.md` and a machine-readable registry.

- **Where the metadata lives.** `lint_v09.py` does not reject unknown keys, but it is not known
  whether harness.design keeps them on upload. Check with the harness.design editing guide
  first. Default: a sidecar `docs/harness/interfaces.yaml` keyed by drawing + component id, so
  the `.harness` files stay pure harness.design JSON.
- **Record fields.** `type` (`real_connector` | `inline_interface` | `oem_flying_lead` |
  `device_endpoint` | `reference_only`), `physicalOwner`, `interfaceId`, `buildOnce`,
  `bomOwner`, and for flying leads `ewd: {page, connector, pin, color, function, method}`.
- **Inline interfaces.** One `interfaceId`, two halves, each naming its owner harness; the
  receiving harness owns the mating half; pin map shared.
- **Drawing convention.** How an endpoint looks in harness.design (a zero-part connector named
  `VRC_REAR_IN_L` etc., no `partId`, no contacts), so existing tools already treat it as
  claiming nothing.
- **SoT.** How non-ECU device circuits (VRC in/out, A/C switch) sit in `sot/channels.csv`
  without fake ECU rows. `validate_sot.py` must accept them.

### Phase 3 — New gates, soft first

Add alongside the old suite, wired into `check_all.py` as a **SOFT** list (report, don't
fail) until the drawings they check exist:

- `validate_interfaces.py` — unique IDs, exactly two halves on different harnesses, pin maps
  agree, no dangling endpoint references.
- `validate_ownership.py` — one owner per conductor/cable, one BOM owner per build-once item,
  `reference_only` claims nothing.
- `validate_oem_endpoints.py` — every flying lead has all EWD fields; no OEM housing in BOM.
- `validate_wheel_speed.py` — per side: two sensor branches, IN-L/IN-R endpoints, one output
  cable (4 cores + drain; front per D1), one inline interface, one ECU spur.
- `verify_connectivity.py` — the replacement for `verify_rebuild.py`: every assigned ECU pin
  in `sot/channels.csv` reaches its device endpoint through declared interfaces, no conductor
  skips an interface between independent harnesses.

Light edits to the kept gates so endpoint records don't read as defects: `lint_v09.py`,
`audit_cavity_parts.py`, `audit_bulkhead_pairs.py`, `audit_pin_names.py` (drop VRC-cavity
assumptions).

### Phase 4 — Rear wheel-speed vertical slice

1. `sot/channels.csv` rows 84-91: VRC rear rows become endpoint rows; add the rear interface
   pin map (D2).
2. New `ST185-WheelSpeed-Rear.harness`: RL/RR drops (`cp_dt2s_ni`, unchanged) as a Y into
   `VRC_REAR_IN_L` / `VRC_REAR_IN_R` endpoints; `VRC_REAR_OUT` endpoint → 4-core + drain cable →
   rear inline half. No `cp_m8_*`, no `cp_xref`.
3. ECU-side rear spur in the ECU/cabin drawing (today `ST185-B-ECU`, all rear pins are loom
   B): mating half → B20, B19, `sp_5v`, `sp_gndout`, drain → `sp_shield_b` (B17).
4. `audit_shields.py`: replace the VRC-shell checks with endpoint-aware ones: IN screens end at
   the VRC enclosure endpoint, output drain on interface pin 5 reaches B17, nothing lands on
   the ABS sensor end.
5. `audit_mating.py`: keep M1-M6; replace M7 with the interface-ownership rule.
6. `buildlist.py` / `buylist.py` v2 alongside the old ones (new filenames), covering at least
   this slice: owner, interface, endpoint type, handoff rows instead of `no route found`,
   interface pair counted once, drain pin counted.
7. `verify_rebuild.py`: add the moved rear conductors as redesign exceptions so it keeps
   guarding everything else. Remove the rear half from `ST185-WheelSpeed.harness`.
8. Rear gates go HARD for this slice.

### Phase 5 — Front wheel-speed

Mirror Phase 4 for `ST185-WheelSpeed-Front.harness` using the D1 result. The front spur
splits under the dash: FL → A23 (loom A), FR → B21 (loom B). Its drain(s) go to A7 / B17 per D1.
Retire `ST185-WheelSpeed.harness` when it is empty. Front gates go HARD.

### Phase 6 — CSB3, OEM flying leads, A/C coolant switch

- CSB3: `cp_csb3_plug` (`HD36-24-33SE`, `0462-201-2031`) as the one `real_connector`; every
  other drawing's reference becomes an interface or `reference_only` record; drop the
  CSB3-side `cp_xref` dummies (e.g. `dm_csb3io_c26` in ClusterLED).
- Loom C: OEM J/B and OEM-device connections (J/B2 2A-3/2D-2 etc., A/C pressure switch)
  → `oem_flying_lead` with EWD locators; no OEM housings in the BOM.
- A/C coolant switch (D5): Engine-A sensor → bulkhead A spare cavity → short cabin branch →
  inline interface → A/C amplifier flying lead. SoT row as a non-ECU circuit.
- `validate_oem_endpoints.py` goes HARD.

### Phase 7 — Harness inventory restructure (after D3)

- Merge A-ECU + B-ECU into the ECU/cabin drawing; the only A↔B crossover is shared ECU
  power/ground.
- Re-split engine files by bulkhead letter; no engine-side crossover between A and B.
- Rear Fuel drawing with its D4 connector; fuel level and pump leave `ST185-B-ECU`.
- `audit_mating.py` / `audit_pin_names.py` / `audit_bulkhead_pairs.py` retargeted to the new
  file names (bulkhead halves are now one cabin drawing + one engine drawing per bulkhead).

### Phase 8 — Flip generators and retire legacy tools

Only after every gate above is HARD and green:

1. v2 build list / buy list replace `buildlist.py` / `buylist.py`; regenerate
   `HARNESS-BUILD-LIST.csv` and `NEED-TO-BUY.md` (generated, never hand-edited).
2. `check_all.py` rewritten to the new gate list; `run_pipeline.bat` calls it instead of the
   mutating scripts.
3. Retire `verify_rebuild.py`, the mutating `fix_cable_parts.py` (or reduce it to a cable
   validator), and `layout_633.py`, then `legacy-prebuild/`. Move them to `archive/` with a
   one-line reason rather than deleting.
4. Remaining `cp_xref` dummies removed; `lint_v09.py` rejects new ones.

### Phase 9 — Propagate to every wiring surface

Per `RECONCILIATION-RULES.md` Rule 1, in the same PR as Phase 8 or directly after it:
`docs/harness/README.md` (file table, pipeline), `AGENTS.md` / `CLAUDE.md` ("nine looms"),
`.cursor/rules/harness-wiring-conventions.mdc`, `docs/SHIELD-RULES.md`,
`RECONCILIATION-RULES.md` SoT table (its stale Signal/Power rows, open since 6.41),
`XTREMEX-IO-TABLE.html` via `sync_io_table.py`, `min/` via `make_min.py`, then upload to
harness.design.

---

## 3. Working rules for every phase

- Branch per phase (`cursor/harness-redesign-<phase>-7e33`), draft PR, merged before the next
  phase starts, so `main` and the local checkout stay in step.
- Commit per logical change; push after every commit; `git pull origin main` before starting
  each phase.
- `python docs/harness/check_all.py` before every commit. A new gate may land SOFT; an
  existing HARD gate never goes soft.
- `docs/research-hub.html` is never committed (bot-owned). `HARNESS-BUILD-LIST.csv` and
  `NEED-TO-BUY.md` are committed only as generator output.
- No CAN ID, frame layout or cluster-visible change. D6 is docs-only.

## 4. Acceptance — which gate proves each criterion

| Criterion (from `DECISIONS.md`) | Proven by |
|---|---|
| No VRC enclosure / M8 connector in wheel-speed files | `validate_wheel_speed.py` (no `cp_m8_*`) |
| Front and rear each one Y harness | `validate_wheel_speed.py` |
| One shielded output interface per side, one real Deutsch connector | `validate_wheel_speed.py` + `validate_interfaces.py` |
| ECU/cabin has exactly one front and one rear spur | `validate_wheel_speed.py` |
| CSB3 ends at `HD36-24-33SE`, CSB3 not drawn | `validate_interfaces.py` |
| OEM endpoints are flying leads with EWD labels, no OEM housings | `validate_oem_endpoints.py` + buy list v2 |
| Every physical section one owner, counted once | `validate_ownership.py` + buy list v2 |
| Bulkhead mating and shield rules pass | `audit_mating.py`, `audit_pin_names.py`, `audit_shields.py` |
| Drains float at device ends, reach the right ECU shield ground | `audit_shields.py` (endpoint-aware) |
| No unexplained cross-loom conductor | `verify_connectivity.py` |
