# Base map apply guide (PCLink)

## What this produces

**One file:** `maps/st185-furyx-base-v1.pclx`

Safe startup tune — starts, idles, drives gently. Not optimized for peak performance. After this, **all tuning happens in PCLink**; you do not need to maintain YAML, Excel, or repo docs for day-to-day parameter changes.

## Order

1. Load a conservative Link G4X **startup map** (Toyota / 4-cyl turbo class if available).
2. Engine constants: 2189 cc, 8.5 CR, firing order, peak-and-hold injectors.
3. Import `config/can/link_g4x_can_setup.lcs`.
4. Pins per `config/io_assignments.yaml` / `SENSOR_WIRING.md`.
5. Triggers per `TRIGGER_COP_SETUP.md` (36-2 + cam sync).
6. **Loose** protection limits from `config/limits.yaml` → `ecu_limits` (startup only).
7. Features as needed for operation: gear on CAN, A/C shed, basic idle — not full race TC/blip polish unless time allows.
8. Table seeds from `config/tables/` as **starting points** — smooth in PCLink until idle is stable.
9. First fire: `OPERATOR_FIRST_START.md`.
10. Short shakedown only — see `STREET_DRIVE_LIMITS.md`.
11. **Save** `st185-furyx-base-v1.pclx`.

## Done when

- [ ] Sync, start, idle 900–1100 RPM without faults
- [ ] Gauges match cluster on CAN
- [ ] No unexpected protection cuts at idle
- [ ] Brief street drive or trailer/dyno trip is reasonable

Dyno optimization is a **later PCLink session**, not this project.

## CAN verify (once)

Cluster on: 0x3E8–0x3EB track; 0x3EE bytes 0–5 show on red overlay when you intentionally test cuts/faults.
