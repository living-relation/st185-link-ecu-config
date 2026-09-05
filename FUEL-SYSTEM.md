# Fuel System — AN Hose & Pump Sizing

Reference notes for fuel delivery sizing on the ST185 5S-GTE build. This is **not** part of the
CAN bus contract (see `README.md` Scope) — informational build reference only, kept here for
convenience alongside the rest of the build documentation.

## Target build

| Parameter | Value |
|---|---|
| Target power | 600 hp |
| Fuel | 93 octane pump gas / E85 |
| Pump | Walbro F90000295 (~450 LPH @ 43 psi rated on gasoline) |

## AN hose sizing rule of thumb (gasoline, single pump/line)

| Target power (gasoline) | Feed | Return |
|---|---|---|
| Up to ~350–400 hp | -6 AN | -6 AN |
| ~400–700 hp | -8 AN | -6 AN |
| ~700–1000 hp | -10 AN | -8 AN |
| 1000+ hp | -12 AN | -8/-10 AN |

**Recommended for this build: -8 AN feed / -6 AN return.**

- E85 needs ~30% more fuel volume than gasoline for the same power, which pushes 600 hp firmly
  into -8 AN feed territory even though the gasoline-only table would place it right at the
  -6/-8 boundary.
- The real constraint is pump flow (LPH) at target pressure, not horsepower directly — an
  undersized line chokes a big pump before horsepower does.
- Return-style systems only need the return line sized to carry excess (unused) fuel, not full
  pump output, so it can run one size smaller than feed.

## Pump capacity note

A single Walbro F90000295 reliably supports roughly 500–550 whp on E85 at stock voltage. For a
600 hp target on E85, consider one of:

- Boosted pump voltage (15–18 V via a voltage controller/relay), or
- A second pump (staged or parallel) for headroom.

The -8 AN feed line sizing above holds either way — it won't be the bottleneck.
