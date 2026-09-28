# Driveability tuning notes

PCLink features to configure after triggers and base VE/ignition seeds. Conservative first — refine from logs.

## Cold start

- Cranking enrichment vs ECT — rich enough for fire, not flood.
- Post-start hold 5–15 s decay — HKS 264 overlap needs adequate cranking fuel.
- **Hot restart** table separate (ECT >160°F soak) — reduce cranking fuel vs cold.
- **Fuel-temp vapor-lock trim:** `tables/warmup_fuel_temp_trim.csv` adds cranking/post-start
  enrichment on top of the ECT tables above once fuel temp (Continental sensor, DI 2) approaches
  the RealDash caution band (55°C) — return-style system + E85 vapor-locks hot, independent of
  ECT (a hot rail can outlast a cooling engine).

## Warm-up

- Post-start enrichment decay vs ECT until closed-loop stable.
- Idle air (ETB target) vs ECT — 900–1100 RPM target band.
- Fuel density: `tables/fuel_temp_density_comp.csv` scales fuel delivery vs fuel temp — apply
  everywhere VE fuel delivery is calculated, not just warm-up (E85 density shifts ~0.1%/°C).

## Idle strategy

- ETB idle primary; idle ignition trim vs ECT secondary.
- **Idle-up offsets:** A/C clutch (+150–250 RPM), Spal fans, alternator load optional.
- See A/C MAP/RPM cutouts in `FEATURES_AC_IDLE_CRUISE_TC.md`.

## Dual IAT

| Sensor | Use |
|--------|-----|
| Manifold IAT | VE/ignition correction, general load |
| Charge-pipe IAT (pre-throttle) | Transient enrichment, tip-in/out, anti-buck when MAP noisy |

Only manifold IAT on cluster CAN today (0x3E8) — charge IAT is ECU-internal.

## Anti-buck / partial throttle

- MAP rate-of-change enrichment limits.
- Accel/decel fuel trims.
- ETB dashpot / trailing throttle ignition retard in overlap regions (264 cams).
- Tune where MAP oscillates at light throttle/cruise.

## EMAP (optional)

If vacuum-reference load is unstable at overlap (sub-30 kPa MAP flutter):

- Add dedicated or shared **EMAP** analog input.
- Compare MAP vs EMAP in logs before hardware commit.
- Not required for first fire.

## Flex fuel blend

- Continental DI 2 → one PWM signal, two decoded values: frequency = ethanol %, pulse width =
  fuel temp. Ethanol% feeds both boost trim (`boost_target_ethanol_mult.csv`) and fuel/ignition
  trim (`multi_fuel_blend.csv`); fuel temp feeds the density/warmup tables (see Warm-up and Cold
  start above).
- Use `multi_fuel_blend.csv` seed; verify ethanol reading vs known E85 sample at tune session.
- **Sensor fault (Ethanol% channel).** Daniel's requirement: on signal loss, the ECU must fall
  back to the pump-gas-safe boost table, never the E85 one — so `boost_target_ethanol_mult.csv`
  falls back to ethanol_pct=**0**. But `multi_fuel_blend.csv` reads the *same* channel, and 0
  there means the *leanest* fuel trim (1.00, no retard) — if the tank is actually high-ethanol,
  that under-fuels by up to 40%, a real detonation risk. A single channel can't hold two values
  at once, so: `multi_fuel_blend.csv` gets the opposite substitute, ethanol_pct=**100** (richest
  fuel trim, most retard — a driveability nuisance on pump gas, not a hazard), and boost safety
  is enforced independently instead — `tune/limits.yaml` → `ecu_limits.boost.ethanol_sensor_fault_cap_psi`
  (18 psi, matching `boost_target_psi.csv`'s street-seed ceiling), gated directly on the PCLink
  Ethanol Sensor Fault flag rather than on the ethanol% value, so it still engages even though
  that value now reads a "full boost is fine" 100%. Configure both in PCLink's Ethanol Sensor
  Fault / DI error handling — never silently hold the last-good value.

## Validation drives

1. Cold start → idle → warm cruise (no boost).  
2. Hot restart after 10 min soak.  
3. Light throttle transitions 1500–3500 RPM (anti-buck).  
4. Single 3rd-gear pull to **12 psi** max — log knock, lambda, oil PSI.
