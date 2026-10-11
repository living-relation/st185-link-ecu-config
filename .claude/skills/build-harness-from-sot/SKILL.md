---
name: build-harness-from-sot
description: Builds or checks one `docs/harness/rebuild/*.harness` file against the wiring source of truth. Use when Dan says "draw the harness for X", "build the .harness file", "check this loom against the SoT", or when a route is approved and ready to become wiring. Covers which SoT inputs to read, the ECU-connector-letter rule, shields, bulkhead sharing, splice sizing, and the `check_all.py` gate. Do NOT use this to decide what to draw before a route is approved (see `apply-route-markup`), and never derive a fact from a `.harness` file itself.
paths:
  - docs/harness/rebuild/**
  - docs/harness/interfaces.json
  - sot/channels.csv
  - docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md
  - docs/SHIELD-RULES.md
  - docs/harness/check_all.py
---
# build-harness-from-sot

## Where to run
- Repo root, `C:\projects\active\st185-link-ecu-config` (or a worktree — coordinate first if another session is mid-harness-pass there). Shell: PowerShell.

## Critical
- **Never derive truth from a `.harness` file.** The looms are drawings of what gets built, not a source of truth (Daniel, 2026-10-04). Read, in this order: `sot/channels.csv` (pin SoT), `docs/harness/interfaces.json` (ownership/boundaries), `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` (device pin + shield flag), the 1993 EWD, and datasheets.
- The ECU connector letter sets the loom and bulkhead (`docs/RECONCILIATION-RULES.md` Rule 3). Four ECU loom files only: `ST185-A-cabin`, `ST185-B-cabin`, `ST185-A-engine`, `ST185-B-engine`. The only crossovers are (a) +5V/Gnd Out, (b) ETB A20/B5, (c) APS A14/B33 — nothing else, enforced by `validate_bulkhead_letter.py`.
- A wire that crosses between harness files is drawn broken off in both, each end noting the other file, or crosses through an `IX_*` inline connector pair. Files are never merged.
- Shields (`docs/SHIELD-RULES.md`): float at the sensor, terminate continuously at the ECU or the destination device — never at a connector shell. A Raychem solder sleeve is only for a shielded cable with no drain wire, never for an unshielded cable or a flying lead.
- A bulkhead cavity is shared only by the same signal/class on both halves — never two different circuits on one cavity (`audit_bh_collisions.py`).
- Splices are sized by combined gauge, not per-wire (4×20 AWG = 14 AWG, Wire Barn Combined Wire Gauge Calculator).
- No OEM engine-bay wire is reused (Daniel, 2026-10-04, binding) — every engine-bay circuit is new wire, terminated at the device's own plug.
- Relays are active-low (the Link G4X output sinks to energize them) and get no external flyback diode — the Link handles that internally. Use G4X documentation only for ECU electrical behavior, never a forum wiring diagram.
- Draw against the latest **approved** route for this harness in `_research\routes` (main checkout) — if it isn't approved yet, that's `apply-route-markup`'s job first.

## Instructions
1. Identify the harness file and its scope from `docs/harness/interfaces.json` and `docs/RECONCILIATION-RULES.md` Rule 1's surface table.
2. Pull every pin/channel in scope from `sot/channels.csv`, cross-checked against `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` for device pin and shield flag.
3. Confirm the latest approved route for this harness in `_research\routes` (main checkout) for physical path and part spots.
4. Draw or update `docs/harness/rebuild/<Harness>.harness`: connector-letter placement, broken-off/`IX_*` boundaries, shield continuity, bulkhead sharing, splice sizing, no-reused-OEM-wire — all per the Critical rules above.
5. Run `python docs/harness/check_all.py` from the repo root. Fix every HARD-gate failure it reports before moving on.
6. If a generator (`buylist.py`, `buildlist.py`, `make_min.py`) reports stale, regenerate it (no flag, or `--write`) and commit the result with the drawing — never hand-edit a generated file.

## Verification
- `python docs/harness/check_all.py` prints "all checks passed".
- The drawing matches the approved route's physical path and part spots; any mismatch between them is written to `docs/OPEN-ITEMS.md`, never left silent.
