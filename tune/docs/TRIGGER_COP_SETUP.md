# Trigger + COP setup

## Hardware

- **Crank (Trigger 1):** OEM Toyota VR on **36-2** crank wheel (multitooth/missing).
- **Cam (Trigger 2):** Cherry Hall, single intake cam tooth — **Cam Pulse 1×**.
- **Ignition:** Toyota 1ZZ COP ×4, sequential.

## PCLink — Trigger 1 (crank)

| Setting | Value |
|---------|-------|
| Trigger Mode | **Multitooth / Missing** |
| Tooth Count | **36** |
| Missing Teeth | **2** |
| Multi-tooth Position | **Crank** |
| Sensor | Reluctor (VR) |

Verify **VR polarity** on Trigger Scope — wrong polarity causes RPM breakup at high speed.

## PCLink — Trigger 2 (cam sync)

| Setting | Value |
|---------|-------|
| Sync Mode | **Cam Pulse 1×** |
| Sensor | Hall (Cherry), rising edge typical |

## Arming and base timing

1. Capture **Trigger Scope** while cranking before first start.
2. VR arming threshold: low values at 0–500 RPM (~0.2–0.3 V) — tune from scope.
3. Base timing procedure per [Link startup maps](https://linkecu.com/getting-started/start-up-maps/) before first fire.
4. Dwell table for 1ZZ COP (~3–4 ms @ 14 V starting point).

## Cam timing reference (HKS 264)

Typical lobe-center baselines for HKS 264° cams:

| Cam | Typical LC |
|-----|------------|
| Intake | **110° ATDC** |
| Exhaust | **103° BTDC** |

272° cams often use 110° intake / 108° exhaust. Some tuners **advance exhaust toward 272° spec** to increase overlap (~13°) for spool and cylinder pressure — document final installed degrees in `ENGINE_SPEC.md`.

## Pre-start checklist

- [ ] Trigger Scope: stable Trig 1 count, clean Trig 2 sync once per 720°
- [ ] No Trig 1 error count climbing at cranking RPM
- [ ] COP wiring and dwell sane at 12–14 V
