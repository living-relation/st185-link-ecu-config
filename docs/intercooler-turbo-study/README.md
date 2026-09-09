# Intercooler, turbo, and charge-piping study

Engineering study for the 5S-GTE ST185 cold side: turbo match, intercooler
core, front-stack order, and charge-pipe sizing. Mechanical/thermal scope,
kept here as the build-reference location.

## Read these

| File | What it is |
|---|---|
| `intercooler-report.html` | Rebuilt deliverable: calculated power, IC thermo, front stack, pipes. |
| `turbo-comparison.html` | Official BorgWarner maps with this engine's MatchBot operating line. |
| `THROTTLE-BODY-PLUMBING-SPEC.md` | Hot 2.50 in / cold 3.00 in pipe spec (unchanged). |
| `model/` | Single source of truth: `inputs.yaml`, MatchBot case/results, IC + power JSON. |

`research/` is the old working trail (scripts, invoices, prior-round backups).
It is not the deliverable. The byte-identical `research/intercooler-report.html`
copy was removed so the root HTML cannot drift again.

## Headline numbers (derived, not targets)

- Turbo: keep EFR 7163-G for a road car; 7670-C if you want 30 psi held in-island to 7500+. 7064 is the wrong compressor.
- Power: ~606 crank / 503 WHP on E85 at 8000 rpm / 27 psi (17% AWD loss). MatchBot pump-gas peak 500 crank at 6000 / 30 psi.
- Intercooler: 4.5 in tube-and-fin, ~27 × 12 in face. Bar-plate is the time-attack core.
- Pipes: 2.50 in OD hot side, 3.00 in OD cold side.

30 psi is max boost, not a required point. Redline is a 7200–8000 band.
93 pump is knock-limited (~22 psi planning ceiling) until a logged pull.

Regenerate reports: `python3 model/ic_stack.py && python3 model/power_limits.py && python3 model/build_reports.py`
