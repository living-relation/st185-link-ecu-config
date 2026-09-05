# Protection and warnings

## Two separate systems (do not merge)

| System | Where | Purpose |
|--------|-------|---------|
| **Red ECU WARNING box** | Right cluster | Six **outcome** flags on CAN **0x3EE bytes 0–5** only |
| **Gauge / arc colors** | Left + right UI | **Cosmetic** — sensor values on 0x3E8–0x3EB |

Arc colors are **not** alarms. They do **not** get ECU “warning” tiers, CAN bytes, or red-box labels.

## Red box — what the six bytes mean

These are **what the ECU did** (or detected), not a list of every sensor that misbehaved:

| Byte | Label | Meaning |
|------|-------|---------|
| 0 | KNOCK | Knock detected / knock strategy active |
| 1 | IGN CUT | ECU is cutting ignition (many possible causes) |
| 2 | FUEL CUT | ECU is cutting fuel (many possible causes) |
| 3 | BOOST CUT | ECU is cutting/limiting boost (many possible causes) |
| 4 | SENSOR ERR | Sensor fault / improbable reading |
| 5 | THROTTLE ERR | ETB/pedal deviation — early warning before hard cut |

**Not red-box labels:** oil pressure low, coolant hot, coolant pressure high, fuel pressure low, IAT hot, lambda lean/rich, fuel low, overboost as its own text, rev limit.

When a limit trips, you may see **KNOCK**, **BOOST CUT**, **FUEL CUT**, **IGN CUT**, etc. — whatever protection Link actually applied — not a separate message per sensor.

## Pressures, temperatures, spikes — ECU only

Configure Link **limits** (and logging) from best practices for this engine. **No** Link “warning” tier mapped to the cluster for these. **No** extra CAN bytes.

| Condition | Cluster | ECU |
|-----------|---------|-----|
| Low oil pressure | Oil gauge/arc color | **Limit** → fuel/ign cut if catastrophic; may also participate in boost cut strategy |
| High/low coolant pressure | Log / optional gauge if wired | **Limit** or fault handling — engine off or derate as programmed; not red-box text |
| ECT overheat | Coolant gauge color | **Limit** only → engine off (fuel/ign cut) |
| Oil temp high | Arc color | **No** limit for cluster on base map |
| Fuel pressure drop | Log | May trigger boost/fuel cut as part of Link strategy → existing bytes |
| IAT / charge temp hot | Gauge color if shown | May trigger boost cut or fuel trim — **BOOST CUT** / cuts, not “IAT HOT” |
| Lambda out of range | Widget color | Lean → knock/cuts; rich → logs/smoke |

**Coolant pressure spikes**, **oil pressure transients**, and similar: handle in the ECU (limit, cut, log). Driver sees gauge color where applicable; red screen only if a **cut byte** or **KNOCK** / **SENSOR ERR** / **THROTTLE ERR** is active.

## Rev limit

Motorsport feature in PCLink. **Not** a cluster warning category. Do not document or map rev limit as its own red-box alarm.

## Throttle / ETB (exception)

Only case with an intentional **two-step** policy: cluster **THROTTLE ERR** (byte 5) for early deviation so you can pull over; separate Link **limit** shuts the engine. See `ALARM_CAN_SPEC.md`.

## Traction control (separate UI)

TC engaging → **orange** indication when implemented (TC strategy working). TC may use ign/boost/fuel internally — those cuts must **not** also light the red **IGN CUT** / **FUEL CUT** / **BOOST CUT** overlay (intentional TC, not fault). Tune-side note for PCLink CAN routing when TC orange is added.

## ECU limits for base tune

**v1 = loose / high** — tolerate tuning error while getting the engine running. See `LIMITS_STARTUP_VS_TUNED.md` and `config/limits.yaml` → `ecu_limits`.

Tighten knock, boost, oil, ECT, and fuel-pressure limits in a **later map** after street stability and dyno. Outcomes surface only through bytes 0–5 above.

**Do not enable for cluster:** lambda limits, oil temp limits, fuel level, per-sensor **warning** tiers, or red-box labels for pressures/temps.

## CAN contract

`config/can/link_g4x_can_setup.json` — **no 0x3EF, no 0x3EE bytes 6–7.**
