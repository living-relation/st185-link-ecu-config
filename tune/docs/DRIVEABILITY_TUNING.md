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
  **fault**, the fallback is gated on ECT instead — see Sensor fault below.

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
  - **Fuel Temp channel** — single substitute, **90°C** (the tables' richest row) — read by
    `fuel_temp_density_comp.csv` and `warmup_fuel_temp_trim.csv`, which agree on direction
    (rich), so no clamp is needed between them. The real risk is the hard Fuel Cut in
    `tune/limits.yaml` (`ecu_limits.fuel_temp_c.limit_c`, 70°C): a sensor fault is plausibly a
    *thermal* failure (heat-damaged wiring/connector), so it's disproportionately likely to
    coincide with a genuinely hot-soak restart — exactly the case these tables exist to protect.
    A weaker substitute (e.g. staying below 70°C to dodge the cut) would under-fuel that exact
    scenario. Instead the cut itself is gated on sensor **validity**
    (`fuel_temp_c.limit_condition`: `fuel_temp_c > 70 AND Ethanol Sensor Fault = false`, the
    same multi-condition pattern `oil_press` already uses), so the fault-substituted 90°C
    cannot self-trigger the cut, while a genuinely valid >70°C reading still can.
    - `fuel_temp_density_comp.csv` uses the 90°C substitute unconditionally on fault — its
      effect is small (max +7%, multiplicative), self-corrects under closed-loop once running,
      and is not a flooding risk even applied to a cold engine.
    - `warmup_fuel_temp_trim.csv` **cannot** use it unconditionally: it's an *additive*
      cranking/post-start enrichment (+20%/+14% at 90°C), and a flex-sensor fault is exactly as
      plausible on a car that's never run today (cold) as one that just came off a hot drive —
      applying it unconditionally on fault would risk flooding / failure to start on an ordinary
      cold start. So the fault-substitute path (only the fault path — a valid sensor reading
      still works as designed, independent of ECT) is additionally gated on ECT already being
      in the hot-restart range (>160°F, the same condition already used for the separate hot
      -restart cranking table above): faulted + ECT low → apply nothing; faulted + ECT high →
      apply the full 90°C fallback. ECT is a separate sensor circuit with no shared fault path.
  Configure all of this in PCLink's Ethanol Sensor Fault / DI error handling — never silently
  hold the last-good value.

## Validation drives

1. Cold start → idle → warm cruise (no boost).  
2. Hot restart after 10 min soak.  
3. Light throttle transitions 1500–3500 RPM (anti-buck).  
4. Single 3rd-gear pull to **12 psi** max — log knock, lambda, oil PSI.
