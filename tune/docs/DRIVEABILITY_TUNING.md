# Driveability tuning notes

PCLink features to configure after triggers and base VE/ignition seeds. Conservative first — refine from logs.

## Cold start

- Cranking enrichment vs ECT — rich enough for fire, not flood.
- Post-start hold 5–15 s decay — HKS 264 overlap needs adequate cranking fuel.
- **Hot restart** table separate (ECT >160°F soak) — reduce cranking fuel vs cold.
- **Fuel-temp vapor-lock trim:** `tables/warmup_fuel_temp_trim.csv` adds cranking/post-start
  enrichment on top of the ECT tables above once fuel temp (Continental sensor, DI 2) approaches
  the RealDash caution band (55°C) — return-style system + E85 vapor-locks hot, independent of
  ECT *when the sensor reading is valid* (a hot rail can outlast a cooling engine). On a sensor
  **fault**, this table intentionally does NOT try to auto-detect hot-vs-cold from other
  sensors — see Sensor fault below for why that turned out to be unreliable, and what it does
  instead.

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
  fuel temp. Four PCLink consumers read it: boost trim (`boost_target_ethanol_mult.csv`),
  fuel/ignition trim (`multi_fuel_blend.csv`), and the fuel-temp axis
  (`fuel_temp_density_comp.csv` + `warmup_fuel_temp_trim.csv`).
- Use `multi_fuel_blend.csv` seed; verify ethanol reading vs known E85 sample at tune session.
- **Sensor fault.** DI 2 decodes to two *separate* channels — Ethanol% (PWM frequency) and
  Fuel Temp (pulse width) — each with its own fault-substitute value. Neither can be "richest
  for every consumer" because one physical channel value feeds multiple tables that don't all
  want the same direction; where that happens, the fix is an independent mechanism, not a
  second value for the same channel.
  - **Ethanol% channel** — single substitute, **100** (not 0) — read by both
    `multi_fuel_blend.csv` and `boost_target_ethanol_mult.csv`:
    - `multi_fuel_blend.csv` at 100 → richest fuel_mult (1.40), most ignition retard (-4.5°).
      Correct and safe: falling back to 0 would apply the *leanest* trim, under-fueling by up
      to 40% if the tank is actually high-ethanol — a real detonation risk. Rich + retarded on
      pump gas is a driveability nuisance, not a hazard.
    - `boost_target_ethanol_mult.csv` **also** reads 100 on the same fault (it's the same
      channel) → mult 1.000 → the full 30 psi curve. That is *not* safe on its own if the real
      fuel is low-octane — but this table gets no separate fault value of its own (a channel
      cannot hold two values at once). Instead, boost is protected by an **independent clamp**:
      `tune/limits.yaml` → `ecu_limits.boost.ethanol_sensor_fault_cap_psi` (18 psi, matching
      `boost_target_psi.csv`'s street-seed ceiling), gated directly on the PCLink Ethanol
      Sensor Fault flag — not on the ethanol% value — so it still engages even though that
      value now reads a "full boost is fine" 100%.
  - **Fuel Temp channel** — read by `fuel_temp_density_comp.csv` and `warmup_fuel_temp_trim.csv`,
    which agree on *direction* (rich) but need different fault handling because of how each one
    applies that richness:
    - `fuel_temp_density_comp.csv`: single substitute, **90°C** (the richest row), applied
      unconditionally on fault. Safe unconditionally because its effect is small (max +7%,
      multiplicative), self-corrects under closed-loop once running, and is not a flooding risk
      even applied to a cold engine.
    - `warmup_fuel_temp_trim.csv`: **cannot** use 90°C unconditionally — it's an *additive*
      cranking/post-start enrichment (+20%/+14% at 90°C), and a flex-sensor fault is exactly as
      plausible on a car that's never run today as one that just came off a hot drive, so
      unconditional max enrichment risks flooding an ordinary cold start.
      **No proxy signal on this car can safely gate it either.** Four review rounds on this PR
      each found a real scenario that broke the previous attempt: unconditional 90°C floods a
      cold start; gating on ECT >160°F loses protection once ECT has cooled below that while the
      rail is still hot (the table's own reason for existing); gating on ECT >100°F is defeated
      by a hot-ambient cold-soak (an engine that never ran can sit above any fixed ECT number
      purely from hot weather); gating on `(ECT − manifold IAT) >20°F` is defeated by underhood
      heat-soak — right after a hot shutdown the intake sits inches from the hot engine with no
      airflow and can heat-soak toward ECT within minutes, collapsing the delta exactly when the
      gate most needs to stay open. The common failure: every available signal can be pushed
      toward "looks hot" or "looks cold" by ambient heat or heat-soak, independent of whether the
      rail is actually hot — because the one measurement that would settle it, fuel_temp_c
      itself, is the one that failed. That's a missing-sensor problem, not a threshold-tuning one.
      **Resolution:** a single moderate, unconditional substitute — **fuel_temp_c=60°C** (8%
      crank / 5% post-start) — sized to bound the worst case in both directions rather than
      optimize one at the other's expense: comparable to `fuel_temp_density_comp.csv`'s own full
      swing (+7%, already accepted as safe cold), so it won't meaningfully flood a cold start;
      meaningfully rich, so it gives partial vapor-lock mitigation on a genuine hot restart —
      while explicitly **not** the full protection a working sensor gives. A fault always shows
      **SENSOR ERR** on the red box (`PROTECTION_AND_WARNINGS.md` byte 4); treat that as a signal
      that automatic hot-restart protection is running at reduced strength, and hold the throttle
      through an immediate post-track restart per normal hot-flood technique if in doubt. If full
      automatic protection through a sensor fault matters, the real fix is a dedicated fuel-rail
      temperature sensor — not a cleverer proxy for the one that failed.
  Configure all of this in PCLink's Ethanol Sensor Fault / DI error handling — never silently
  hold the last-good value.

## Validation drives

1. Cold start → idle → warm cruise (no boost).  
2. Hot restart after 10 min soak.  
3. Light throttle transitions 1500–3500 RPM (anti-buck).  
4. Single 3rd-gear pull to **12 psi** max — log knock, lambda, oil PSI.
