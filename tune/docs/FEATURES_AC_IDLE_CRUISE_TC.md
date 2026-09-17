# Features — A/C, idle, cruise, TC, shift

## A/C compressor (MAP + RPM)

**Cut** when MAP gauge **> 17 PSI** OR RPM **> 5000**.  
**Re-engage** when MAP **< 14 PSI** AND RPM **< 4500** for **≥ 3 s**.

Also require: A/C request, idle RPM floor, valid high-side pressure, evap above freeze.

Idle-up: +150–250 RPM when clutch on at low MAP.

Fans: ECT + head-pressure override when A/C on.

## Gear display + neutral

- Clutch in: **hold** gear (no N flash).
- Reverse DI active → **R** on 0x3EB.
- N: idle RPM clutch out, or ratio mismatch debounce.
- Ratio fault: N only; **no** driver warning.

## Upshift cut (contextual)

Enable when: clutch + TPS high + RPM in top band for current gear + vehicle accel ≥0.

## Downshift blip (ETB, always when context matches)

Clutch + low TPS + decel → ETB blip to sync RPM for lower gear from speed tables.

## Traction control

4× wheel speed DI; cluster **0x3ED** selects slip map. TC is ECU-internal — **no** extra CAN alarm byte for TC overlay.

## Cruise (optional — not required for startup map)

ST185 EWD p116–121: OEM stalk resistor ladder → **AN9** if spare.

| Function | Approx. resistance |
|----------|-------------------|
| Cancel | ~413 Ω |
| Resume | ~68 Ω |
| Set | ~198 Ω |

Pins 5–17 (cruise) vs 15–17 (main). Configure Link cruise after base idle is stable.

## Validation tests

Documented in `AGENT_SESSION_CONTEXT.md` (clutch hold, hidden neutral, reverse switch, ratio fault invisible).
