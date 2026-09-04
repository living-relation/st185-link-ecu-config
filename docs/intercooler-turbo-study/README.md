# Intercooler, turbo, and charge-piping study

Engineering study for the 5S-GTE ST185 build's cold-side hardware: intercooler
core selection, turbo/redline selection, and charge-pipe (throttle body
plumbing) sizing. This is mechanical/thermal scope, separate from the CAN/ECU
config that is this repo's primary subject — kept here for a single
build-reference location.

## Files

| File | What it is |
|---|---|
| `intercooler-report.html` | The deliverable. Self-contained (inline CSS/JS/charts, no internet needed) — double-click to open. 24 sections, 27 charts, 2 calculators covering core selection, turbo/redline choice, manifold pairing, boost control, and open build questions. |
| `THROTTLE-BODY-PLUMBING-SPEC.md` | Charge pipe sizing (hot side 2.5 in OD, cold side 3.0 in OD), velocity/pressure-drop tables, bend radii, and the parts list for the throttle body plumbing run. Cross-referenced from the report. |

## Headline numbers (see the report for full derivation)

- Turbo: keep the BorgWarner EFR 7163. Redline 7,200 rpm (7,500 outer limit).
- Power: ~404 whp / 505 crank at 7,500 rpm, 30 psi on E85.
- Intercooler core: 610 x 305 x 102 mm bar & plate, single pass.
- Charge piping: 2.50 in OD hot side, 3.00 in OD cold side (both 0.065 in wall).
- Manifold: re-pair to 1+4 / 2+3 before dyno tuning (currently paired 1+2 / 3+4).

Both documents carry their own error bands and open questions — read those
sections before ordering hardware.

Source research (build/verification scripts, prior-round backups, raw
invoice/OCR inputs) lives outside this repo.
