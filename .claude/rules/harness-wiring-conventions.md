# Harness Wiring Conventions

**Canonical text: `docs/RECONCILIATION-RULES.md` Rule 1. Read it before finalizing any wiring
change.** This file is a pointer plus the facts most often got wrong — it is deliberately not
a second copy, so the two cannot drift apart.

## The rule

A change to one wiring document is not done until it is checked against the source-of-truth
chain **and every other wiring surface**, including the ones you did not edit. They must all
agree. `python docs/harness/check_all.py` must pass before every commit.

## Source of truth

`sot/channels.csv` is the pin source of truth. New pin facts go into it first; if anything
disagrees with it, the other thing is wrong. `XTREMEX-IO-TABLE.html` is its visual face
(gated by `sync_io_table.py`).

The looms, `docs/harness/rebuild/*.harness`, are drawings of what gets built. **They are not a
source of truth** (Daniel, 2026-10-04): they must agree with the SoT, and no truth document is
ever generated from them. `docs/harness/min/` and the harness.design app copy are copies of
the drawings (mirror only, never edit as source).

## Facts that are commonly stale

- **Two bulkheads only**, A and B, HDP20 from owned stock: A is `HDP24-24-47PE-L017` /
  `HDP26-24-47SE-L015`, B is `HDP24-24-21PN` / `HDP26-24-21SN`. Bulkhead C is deleted. The
  Souriau 8STA 37-way design is superseded — do not reintroduce it.
- **ECU looms follow the ECU connector letter** - canonical text `docs/RECONCILIATION-RULES.md`
  Rule 3 (Daniel, 2026-09-28; overrides "A = signal / B = power" and the merged ECU-Cabin).
  Four ECU files: `ST185-A-cabin`, `-B-cabin`, `-A-engine`, `-B-engine`; the letter is the
  pin's `conn` column in `sot/channels.csv`; non-ECU wires follow their device's ECU signal.
  Only crossovers: (a) +5V (A32) spliced to both bulkheads - sensor ground stays per letter
  (A24 on A, B22 on B, never tied), (b) ETB A20 / B5, (c) APS A14 / B33. Gate:
  `validate_bulkhead_letter.py`.
- **Part descriptions describe the part, never its use.** One format: `TYPE, SUBTYPE, key
  ratings`, uppercase, no nets, circuits, devices, groups, layers, sensors, signals, stock
  counts or plan references. Wires are generated from gauge/colour. Gate: `part_desc.py`
  (`--fix` rewrites to the standard text).
- **Each bulkhead cavity mates its twin.** Bulkhead A cabin cN = bulkhead A engine cN, same
  for B, same name on both halves. The looms are separate drawings, so only the audits join
  them (`audit_mating.py`, `audit_pin_names.py`).
- **One file, one physical harness** (redesign 2026-09-27). The harnesses are the files in
  `docs/harness/rebuild/`; who owns what, and every boundary, is in `docs/harness/interfaces.json`
  (`docs/harness/redesign/INTERFACES.md`). Crossings are inline connector pairs, bulkheads,
  OEM flying leads with EWD locators, or registered references. Devices (VRC, CSB3, OEM
  modules) are never drawn.
- **Harness C is the Engine Room Harness** — no bulkhead, exits the driver fender around the
  front of the bay. The front wheel-speed drops follow its fender route (drawn in
  `ST185-WheelSpeed-Front.harness`) and never touch a bulkhead.
- **CAN H/L is drawn once**, in `ST185-CAN.harness`. No other loom draws it.
- **Shields** float at the sensor and terminate at the ECU or at the destination
  device. Screen means shield. A drain is the wire that connects the shield to
  the pin. Full rules: `docs/SHIELD-RULES.md`.

Full build rules: `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` §6.
