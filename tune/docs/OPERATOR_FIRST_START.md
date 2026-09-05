# Operator first-start procedure

Human checklist — **not** an ECU alarm path. Perform with fuel/pump/ignition safeties understood.

## Before cranking

1. **Battery** charged; ECU harness continuity checked.
2. **Oil** filled (10W-50), cooler plumbed, no leaks.
3. **Coolant** full, burped, no leaks.
4. **Fuel** system primed — Walbro on, rail pressure verified at Chase Bays setpoint.
5. **Triggers:** Trigger Scope captured — 36-2 crank clean, Cam Pulse 1× sync. VR polarity verified.
6. **Base timing** set per Link procedure (timing light / locked timing mode).
7. **Coils/plugs** wired sequential 1ZZ COP; injectors phased correctly.
8. **ETB** calibrated — pedal + throttle min/max, no fault codes.
9. **Wideband** reading sane in air (LSU warmup).
10. **Cluster** powered on CAN1 @ 1 Mbit/s — verify 0x3E8–0x3EB after first fire.

## First crank (no start expected first try is OK)

- Crank ≤10 s bursts, 30 s rest — watch oil pressure rise on gauge/log.
- No fuel smell at exhaust; fix leaks before retry.
- If no sync: stop — re-check Trigger Scope, do not keep cranking dry.

## First idle (target 900–1100 RPM ETB idle)

- **No boost** — wastegate/spring verified, MAC valve plumbed, boost target table low.
- **Rev limit** soft — 4000 RPM max until oil temp and trims stable.
- Log: ECT, oil PSI, oil temp, lambda, MAP, IAT×2, ETH% if flex connected.

## First 10 minutes

- Do **not** rev past 3000 until oil temp >160°F.
- Confirm fan kick-in, no coolant boil, no knock counts climbing at idle.
- **Log hot-idle oil PSI** @ oil temp ≥180°F → `ENGINE_SPEC.md` for later tune. v1 oil limit stays **loose** (`limits.yaml`).

## Abort if

- Oil pressure does not rise within 3 s of cranking.
- Coolant leak, fuel leak, or sustained lambda <0.65 at idle.
- Trig errors, sync loss, or ETB fault codes.

## After successful idle

- Short **no-load** rev to 3500 — confirm pressure rises, no misfire.
- **Street drive limits** apply until dyno (`STREET_DRIVE_LIMITS.md`).
