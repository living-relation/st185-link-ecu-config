---
name: change-sot
description: Edits `sot/channels.csv` or `docs/harness/interfaces.json` — the wiring/CAN pin source of truth — and propagates the change. Use when Dan asks to add/change an ECU pin, channel, or ownership fact, or says "update the SoT", "add a channel", "change interfaces.json". Covers the required check sequence and which harness files now need a redraw. Do NOT use this to edit a `.harness` file directly (see `build-harness-from-sot`) or a CAN frame contract (see `update-can-frame-contract`).
paths:
  - sot/channels.csv
  - docs/harness/interfaces.json
  - docs/OPEN-ITEMS.md
---
# change-sot

## Where to run
- Repo root, `C:\projects\active\st185-link-ecu-config`. Shell: PowerShell.

## Critical
- `sot/channels.csv` is the ECU pin/channel source of truth; new pin facts go here first (Daniel, 2026-09-25) — never into a `.harness` file or `XTREMEX-IO-TABLE.html` directly.
- `docs/harness/interfaces.json` is the ownership registry (which physical harness owns what, inline interfaces, breaks). Edit it alongside the drawings; it is hand-edited, never generated.
- A SoT change is not done until `docs/harness/check_all.py`, `bench/check_parity.py`, `tune/scripts/validate_tune.py`, and `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py` all run clean, together, in the same pass.
- A mismatch found and not fixed in the same pass gets written down in `docs/OPEN-ITEMS.md` — never left silent (`docs/RECONCILIATION-RULES.md`).

## Instructions
1. Edit the exact row(s) in `sot/channels.csv` and/or the exact key(s) in `docs/harness/interfaces.json`. Keep existing column/key style; don't restructure unrelated rows.
2. Run, together, in the same pass:
   - `python docs/harness/check_all.py`
   - `python bench/check_parity.py`
   - `python tune/scripts/validate_tune.py`
   - `python -m py_compile bench/frames.py bench/can_bench.py apps/trackcluster-can-sender/app.py`
3. From `docs/RECONCILIATION-RULES.md` Rule 1's surface table, list every `docs/harness/rebuild/*.harness` file whose scope covers the changed connector letter/pin — that's what still needs a redraw via `build-harness-from-sot`.
4. If a listed harness file won't be updated in this same change, add a row to `docs/OPEN-ITEMS.md` naming the file and what's now stale in it.

## Verification
- All four commands in step 2 exit clean.
- Every downstream harness file from step 3 is either updated in the same change or logged in `docs/OPEN-ITEMS.md`.
