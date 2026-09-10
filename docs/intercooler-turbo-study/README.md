# Intercooler, turbo, and charge-piping study

Engineering study for the 5S-GTE ST185 cold side: turbo match, intercooler
core, front-stack order, and charge-pipe sizing. Mechanical/thermal scope,
kept here as the build-reference location.

## Read these

| File | What it is |
|---|---|
| `intercooler-report.html` | Deliverable: calculated power (93 / 50/50 / E85, dry vs WMI), IC thermo, FPI, front stack, 2.50 in pipes. |
| `turbo-comparison.html` | Official BorgWarner maps with this engine's MatchBot operating line. |
| `THROTTLE-BODY-PLUMBING-SPEC.md` | Rev 3: 2.50 in both sides. 3.00 in cold withdrawn (volume / lag). |
| `model/` | Single source of truth: `inputs.yaml`, MatchBot case/results, IC + pipes + power JSON. |

`research/` is the old working trail (scripts, invoices, prior-turbo sources).
It is not the deliverable. Round 1/2/3/5 `.bak.html` copies and
`PATCH-NOTE-intercooler-report.md` were removed after the 2026-09-09 rebuild.

## Headline numbers (derived, not targets)

- Turbo: keep EFR 7163-G for a road car; 7670-C if you want 30 psi held in-island to 7500+. 7064 is the wrong compressor.
- Power from the rpm×boost grid (knock ceilings applied): E85 **658 / 649** crank (WMI / dry) at 8000 / 30; 50/50 (~E42) **634 / 550**; 93 **572 / 484** (WMI at 27 psi, dry at 22 psi). WHP = crank × 0.83.
- Intercooler: 4.5 in tube-and-fin, ~27 × 12 in face, **12 FPI**. Bar-plate (time-attack) at **10 FPI**.
- Pipes: **2.50 in OD both sides**. At 55.13 lb/min the 2.50 in hot pipe is 228 ft/s (Garrett 200–300). 3.00 in cold adds ~2.0 L / ~14 ms and is withdrawn.

30 psi is max boost, not a required point. Redline is a 7200–8000 band.
93 pump is knock-limited (~22 psi dry) until WMI / a logged pull.

Regenerate reports:

```bash
python3 model/ic_stack.py && python3 model/pipes.py && python3 model/power_limits.py && python3 model/build_reports.py
python3 ../build-research-hub.py
```
