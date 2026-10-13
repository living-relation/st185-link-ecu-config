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

ST185 EWD p.116 (book p.118), combination switch C14, three wires - full detail in `ECUMASTER_SWITCHBOARD_SETUP.md` Step 4.1 and DECISIONS S23. The ladder goes to CSB3 Analog 2, not an ECU An Volt.

| Function | Resistance to ground | Wire |
|----------|-------------------|------|
| RES/ACC (hold = accelerate) | ~68 ohm | pin 5 W (ladder) |
| SET/COAST (hold = decelerate) | ~198 ohm | pin 5 W (ladder) |
| CANCEL | ~418 ohm | pin 5 W (ladder) |
| MAIN on/off | contact to ground | pin 15 Y-B -> CSB3 S3 |
| Ground | - | pin 17 BR |

Configure Link cruise after base idle is stable.

## Validation tests

Documented in `AGENT_SESSION_CONTEXT.md` (a session note that was not imported into this repo; clutch hold, hidden neutral, reverse switch, ratio fault invisible).
