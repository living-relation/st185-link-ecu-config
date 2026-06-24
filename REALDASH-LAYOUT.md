# RealDash Layout Design — ST185 TrackCluster

Buildable dashboard design for the **Raspberry Pi RealDash** secondary display on the 1993 Celica
GT-Four (3S-GTE) track build. This document is the spec you build against in the RealDash visual
editor; it pairs 1:1 with the inputs defined in [`link_g4x_realdash.xml`](link_g4x_realdash.xml).

> **Why a spec and not a `.rd` file?** RealDash dashboards (`.rd`) are a binary format produced only
> by the in-app visual editor — *"No XML needed of any kind when designing dashboards; XMLs are just
> for specifying custom connections"* (RealDash devs). So the layout is version-controlled here as a
> precise, buildable spec plus the importable channel-description XML it binds to.

---

## 1. Design principles

RealDash is the **secondary** display. The ESP32 center cluster already shows the primary vitals —
RPM, boost/MGP, ECT, IAT, oil temp/pressure, vehicle speed, gear, **actual** lambda, fuel level, and
the full-screen engine-protection warnings (0x3E8–0x3EE). **RealDash must not duplicate those.**

It exists to surface the data the cluster does **not**: driver-assist state (boost map, TC, cruise,
AC), extended sensors (fuel temp, charge-pipe IAT, coolant pressure, ethanol, turbo speed, engine
load, cabin temp), trigger-error health, and the IMU (g-force). See
[`CAN-BUS-MASTER-DESIGN.md`](CAN-BUS-MASTER-DESIGN.md) §7.

Track-display rules followed throughout:

- **Glanceable** — a value should be readable in < 0.5 s of peripheral vision.
- **Dark, high-contrast** — black background, off-white numerals, color reserved for state.
- **Color = meaning** — neutral when OK; amber = caution; red = act now; blue = informational/on.
- **Big where it matters** — driver-assist + the two heat-soak killers (charge-pipe IAT, coolant
  pressure) get the largest tiles.
- **No duplication** — anything already on the cluster is omitted on purpose.

---

## 2. Hardware & canvas

| Property | Value |
|---|---|
| Device | Raspberry Pi 4+/Pi 5 running RealDash |
| Screen | 7" panel, **800 × 480** landscape (the project docs also say "840×480"; design proportionally and let RealDash auto-fit) |
| CAN | USB-CAN adapter (CANable / PCAN), **1 Mbit/s**, passive listener, `bus="0"` |
| Connection XML | `link_g4x_realdash.xml` (RealDash CAN v2, BigEndian) |
| Pages | 3 swipeable pages + a persistent top status strip |
| Orientation | Landscape, fixed |

All coordinates below are in an **800 × 480** design grid (origin top-left, `x,y,w,h` in px).
RealDash scales the finished dash to the physical panel, so treat px as proportional guidance, not
pixel-perfect law. Margin = 16 px, inter-tile gutter = 12 px.

---

## 3. Input inventory

Every gauge binds to a custom input from `link_g4x_realdash.xml` (RealDash **Settings → Inputs →
ECU Specific**, all prefixed `ST185:`). Built-in unit conversion is enabled only where a real
RealDash unit exists (temps → `C`, so you can switch to °F per-gauge).

| Input name | Frame | Raw → value | Display unit | Page |
|---|---|---|---|---|
| `ST185: Target Lambda` | 0x3EF | V×0.001 | λ | Drive |
| `ST185: Throttle` | 0x3EF | V | % | Drive |
| `ST185: TC Setting` | 0x3EF | index 0–4 | — | Drive |
| `ST185: TC Intervention` | 0x3EF | V | % | Drive |
| `ST185: Boost Map` | 0x3EF | index 0–3 | — | Drive |
| `ST185: Cruise State` | 0x3EF | enum | text | Drive |
| `ST185: AC Status` | 0x3EF | enum | text | Drive |
| `ST185: Fuel Temp` | 0x3F0 | V−50 | °C | Sensors |
| `ST185: Engine Load` | 0x3F0 | V | % | Sensors |
| `ST185: Coolant Pressure` | 0x3F0 | V | kPa | Sensors |
| `ST185: Ethanol` | 0x3F0 | V | % | Sensors |
| `ST185: Charge-Pipe IAT` | 0x3F0 | V−50 | °C | Sensors |
| `ST185: Cabin Temp` | 0x3F0 | V−50 | °C | Sensors |
| `ST185: Turbo Speed` | 0x3F0 | V×100 | RPM | Sensors |
| `ST185: Trigger Errors` | 0x3F0 | V | count | Sensors / strip |
| `ST185: Accel X` | 0x3F1 | V×0.1 (signed) | g (longitudinal) | G-Force |
| `ST185: Accel Y` | 0x3F1 | V×0.1 (signed) | g (lateral) | G-Force |
| `ST185: Accel Z` | 0x3F1 | V×0.1 (signed) | g (vertical) | G-Force |
| `ST185: Warn Bits` | 0x3F1 | raw byte | bitmask | strip (raw) |
| `ST185: Flat Shift` | 0x3F1 | bit0 | 0/1 | strip |
| `ST185: Radiator Fan` | 0x3F1 | bit1 | 0/1 | strip |
| `ST185: Low Fuel` | 0x3F1 | bit2 | 0/1 | strip |
| `ST185: High Coolant Press` | 0x3F1 | bit3 | 0/1 | strip / alarm |
| `ST185: Low Oil Press 2` | 0x3F1 | bit4 | 0/1 | strip / alarm |
| `ST185: Switchboard Fault` | 0x3F1 | bit5 | 0/1 | strip |

> **Optional:** to drive RealDash's built-in gauges/units instead of custom inputs, map these to
> built-in target IDs under **Settings → Units & Values → Input Mapping** (e.g. Throttle → TPS).
> The custom-input approach above keeps the dash self-contained — no external mapping required.

---

## 4. Global theme

| Token | Hex | Use |
|---|---|---|
| `bg` | `#0A0C10` | page background |
| `panel` | `#12161D` | tile background |
| `panel-edge` | `#1F2733` | tile border / inactive gauge arc |
| `text` | `#F5F7FA` | primary numerals |
| `text-dim` | `#8A94A6` | labels, units |
| `ok` | `#22D3EE` | normal/active accent (cyan) |
| `good` | `#34D399` | in-spec green |
| `caution` | `#F59E0B` | amber warning band |
| `alarm` | `#EF4444` | red alarm band / overlay |
| `info` | `#3B82F6` | informational on-state (fan, flat-shift) |

**Typography**

- **Numerals:** condensed bold, 7-seg or `DSEG`-style for the hero numbers; size 56–88 px on Drive
  heroes, 36–48 px on Sensors tiles.
- **Labels:** uppercase, letter-spaced ~2 px, `text-dim`, 14–18 px, above each value.
- **Units:** `text-dim`, 50–60% of the numeral size, trailing the value.

---

## 5. Top status strip (all pages)

Persistent strip, `x0 y0 w800 h64`, background `panel`, 1 px bottom border `panel-edge`.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  DRIVE        [FLAT] [FAN] [LOFUEL] [SBFLT]            ⚠ COOLANT P   ⚠ OIL P 2   │ 64px
└───────────────────────────────────────────────────────────────────────────────┘
   page label      info indicators (blue/amber)            critical indicators (red)
```

| Element | x,y,w,h | Input | Behavior |
|---|---|---|---|
| Page label | 16,18,160,28 | — | Static text per page ("DRIVE" / "SENSORS" / "G-FORCE") |
| `FLAT` indicator | 200,16,72,32 | `ST185: Flat Shift` | `info` blue when 1, hidden/dim when 0 |
| `FAN` indicator | 280,16,64,32 | `ST185: Radiator Fan` | `info` blue when 1 |
| `LOFUEL` indicator | 352,16,96,32 | `ST185: Low Fuel` | `caution` amber when 1 |
| `SBFLT` indicator | 456,16,80,32 | `ST185: Switchboard Fault` | `caution` amber when 1 |
| `COOLANT P` indicator | 560,16,116,32 | `ST185: High Coolant Press` | `alarm` red when 1 (also triggers overlay) |
| `OIL P 2` indicator | 684,16,100,32 | `ST185: Low Oil Press 2` | `alarm` red when 1 (also triggers overlay) |

> **Scope reminder:** primary engine-protection alarms (knock, ign/fuel/boost cut, primary oil
> pressure, over-temp) live on the **cluster** (0x3EE full-screen overlay). This strip only carries
> the RealDash-side 0x3F1 bits. Keep the driver's mental model: cluster = engine protection,
> RealDash = assist state + extended sensors.

---

## 6. Page 1 — DRIVE (default page)

The at-a-glance track page: driver-assist state up top, tune/comfort state below.

```
┌──────────────────────── TOP STATUS STRIP (§5) ────────────────────────┐ y0  h64
├───────────────────┬───────────────────┬──────────────────────────────┤
│  BOOST MAP        │  TC SETTING        │  THROTTLE                     │
│                   │                    │                              ▐│
│        2          │        3           │        87 %               ▐▐▐│ y80 h190
│   "MAP 2"         │  intervention 12%  │  (vertical bar + value)   ▐▐▐│
│   ▭▭▭□            │  ▭▭▭▭□  bar        │                           ▐▐▐│
├───────────────────┼───────────────────┼──────────────────────────────┤
│  TARGET LAMBDA    │  CRUISE            │  A/C                          │
│                   │                    │                               │
│      0.88 λ       │       SET          │        ON                     │ y286 h170
│                   │   (enum text)      │   (enum text + icon)          │
└───────────────────┴───────────────────┴──────────────────────────────┘ y480
```

| # | Tile | Gauge type | Input | Range | x,y,w,h | States / alarms |
|---|---|---|---|---|---|---|
| 1 | Boost Map | Numerical (huge index) + label | `ST185: Boost Map` | 0–3 | 16,80,240,190 | `ok` cyan numeral. Optional `enum`/text layer: 0=LOW,1=MID,2=HIGH,3=MAX |
| 2 | TC Setting | Numerical (huge index) | `ST185: TC Setting` | 0–4 | 268,80,240,190 | `ok` cyan. Higher index = looser/lower TC per tune |
| 2b | TC Intervention | Horizontal bar (inside tile 2, bottom) | `ST185: TC Intervention` | 0–100 % | 268,236,240,26 | `good` <10, `caution` 10–40, `alarm` >40 (low grip) |
| 3 | Throttle | Vertical bar + numeric | `ST185: Throttle` | 0–100 % | 520,80,264,190 | `ok` cyan bar; no alarm (driver input) |
| 4 | Target Lambda | Numerical | `ST185: Target Lambda` | 0.60–1.30 λ | 16,286,240,170 | neutral `text`; 2 decimals. Informational (tune target) |
| 5 | Cruise State | Text (enum) + icon | `ST185: Cruise State` | enum | 268,286,240,170 | `text-dim` OFF; `ok` cyan SET/RES; amber OVR |
| 6 | A/C Status | Text (enum) + icon | `ST185: AC Status` | enum | 520,286,264,170 | `text-dim` OFF; `ok` ON; `alarm` FLT |

Enum text comes straight from the XML (`Cruise State`: OFF/STBY/SET/RES/OVR; `AC Status`:
OFF/REQ/ON/FLT). In RealDash bind the gauge to the input and enable **Show as text / enum**.

---

## 7. Page 2 — SENSORS

Eight extended-sensor tiles in a 4 × 2 grid. Top row = heat-soak & load (most track-critical);
bottom row = fluids, cabin, and ECU health.

```
┌──────────────────────── TOP STATUS STRIP (§5) ────────────────────────┐ y0  h64
├───────────┬───────────┬───────────┬───────────────────────────────────┤
│ CHARGE IAT│ COOLANT P │ TURBO SPD │ ENGINE LOAD                        │ y80
│   round   │   round   │   round   │   bar + %                          │ h190
│  52 °C    │ 110 kPa   │ 132k rpm  │   64 %                             │
├───────────┼───────────┼───────────┼───────────────────────────────────┤
│ FUEL TEMP │ ETHANOL   │ CABIN     │ TRIGGER ERRORS                     │ y286
│   round   │   bar %   │  numeric  │   numeric (0 = healthy)            │ h190
│  46 °C    │  E30      │  24 °C    │   0                                │
└───────────┴───────────┴───────────┴───────────────────────────────────┘ y480
```

Tile width 183, gutter 12 → x columns: **16 / 211 / 406 / 601**.

| # | Tile | Gauge type | Input | Range | OK | Caution (amber) | Alarm (red) | x,y,w,h |
|---|---|---|---|---|---|---|---|---|
| 1 | Charge-Pipe IAT | Round needle + value | `ST185: Charge-Pipe IAT` | 0–80 °C | <50 | 50–60 | >60 (heat soak → pull timing) | 16,80,183,190 |
| 2 | Coolant Pressure | Round needle + value | `ST185: Coolant Pressure` | 0–300 kPa | 50–150 | 150–200 | >200 or `High Coolant Press`=1 | 211,80,183,190 |
| 3 | Turbo Speed | Round needle + value | `ST185: Turbo Speed` | 0–200k RPM | <90% | 90–95% | >95% of turbo max (set to your turbo) | 406,80,183,190 |
| 4 | Engine Load | Horizontal bar + value | `ST185: Engine Load` | 0–100 % | any | — | — (informational) | 601,80,183,190 |
| 5 | Fuel Temp | Round needle + value | `ST185: Fuel Temp` | 0–90 °C | <55 | 55–70 | >70 (vapor/lean risk) | 16,286,183,190 |
| 6 | Ethanol % | Horizontal bar + value | `ST185: Ethanol` | 0–100 % | any | — | — (flex-blend reference) | 211,286,183,190 |
| 7 | Cabin Temp | Numerical | `ST185: Cabin Temp` | −10–60 °C | any | — | — (comfort, optional) | 406,286,183,190 |
| 8 | Trigger Errors | Numerical (large) | `ST185: Trigger Errors` | 0–255 | =0 | 1–4 | ≥5 or rising (sync loss) | 601,286,183,190 |

> Turbo Speed redline depends on the fitted turbo (e.g. a small-frame CT/Garrett can spin past
> 150k). Set the round-gauge caution/alarm angles to **your** turbo's max RPM in Look'n'Feel →
> Special → Autoscaling; the 200k range here is a safe upper bound.

---

## 8. Page 3 — G-FORCE (IMU)

Traction page: a g-ball (lateral vs longitudinal) with live dot + peak hold, flanked by per-axis
bars. Great for braking/turn-in feedback and chassis debugging.

```
┌──────────────────────── TOP STATUS STRIP (§5) ────────────────────────┐ y0  h64
├──────────┬───────────────────────────────────────────────┬───────────┤
│  LONG  X │                  G-BALL                         │ VERT   Z  │
│  ▲       │              ╭───────────────╮                  │   ▲       │
│  bar     │           ╭──┤    rings at   ├──╮               │   bar     │ y80
│  +0.32 g │           │  │  0.5/1.0/1.5g │  │               │  1.02 g   │ h390
│          │           ╰──┤      • dot    ├──╯               │           │
│  LAT   Y │              ╰───────────────╯                  │  peak     │
│  bar     │        peak: 1.18 g lat / 1.05 g brake          │  1.30 g   │
└──────────┴───────────────────────────────────────────────┴───────────┘ y480
```

| # | Element | Gauge type | Input(s) | Range | x,y,w,h | Notes |
|---|---|---|---|---|---|---|
| 1 | G-Ball ring | Static image/shape (3 concentric rings + crosshair) | — | ±1.5 g | 240,84,320,320 | Rings label 0.5 / 1.0 / 1.5 g |
| 2 | G-Ball dot | Indicator (filled circle) moved by animation | X=`Accel Y` (lat), Y=`Accel X` (long) | ±1.5 g → ±150 px | centered in #1 | See build note below |
| 3 | Long (X) bar | Vertical bar, bipolar + value | `ST185: Accel X` | −1.5…+1.5 g | 16,80,96,390 | +accel up / −brake down |
| 4 | Lat (Y) value | Numerical (under X bar) | `ST185: Accel Y` | −1.5…+1.5 g | 16,300,96,80 | |
| 5 | Vert (Z) bar | Vertical bar + value | `ST185: Accel Z` | 0…+2.0 g | 688,80,96,390 | curb/kerb strike & load |
| 6 | Peak hold text | Text + max-hold trigger | `Accel X/Y` | — | 240,410,320,60 | RealDash trigger: store max(abs) to a custom value; "Reset" on tap |

**Building the g-ball dot (RealDash editor):**

1. Add a small filled-circle **Indicator** gauge (the dot), placed at the ring center.
2. Open **Edit → Animations** and add two **position** animations on the dot:
   - **X position** ← input `ST185: Accel Y` (lateral), input range −1.5…+1.5 g mapped to −150…+150 px.
   - **Y position** ← input `ST185: Accel X` (longitudinal), input range −1.5…+1.5 g mapped to
     **+150…−150 px** (invert so braking = dot toward bottom, accel = top).
3. Clamp travel to the ring radius (150 px) so it can't leave the circle.
4. Animations are saved into the `.rd`; if you prefer to version them as text, export them to
   `realdash_st185_anim.xml` (named `<dashboardname>_anim.xml`) — see RealDash-extras animation
   examples: <https://github.com/janimm/RealDash-extras/tree/master/Dashboard-animation-examples>.

---

## 9. Alarm & warning logic

Priority high→low. The two **critical** bits also raise a full-width modal overlay; the rest stay as
strip indicators only.

| Priority | Condition | Source | Indicator | Color | Overlay? |
|---|---|---|---|---|---|
| 1 | Low oil pressure (secondary threshold) | `ST185: Low Oil Press 2` =1 | `OIL P 2` | `alarm` red, blink | **Yes** |
| 2 | High coolant pressure | `ST185: High Coolant Press` =1 | `COOLANT P` | `alarm` red, blink | **Yes** |
| 3 | Trigger errors rising | `ST185: Trigger Errors` ≥5 | Sensors tile #8 | `alarm` red | No |
| 4 | Switchboard / accessory bus comm fault | `ST185: Switchboard Fault` =1 | `SBFLT` | `caution` amber | No |
| 5 | Low fuel | `ST185: Low Fuel` =1 | `LOFUEL` | `caution` amber | No |
| 6 | Radiator fan on | `ST185: Radiator Fan` =1 | `FAN` | `info` blue | No |
| 7 | Flat-shift active | `ST185: Flat Shift` =1 | `FLAT` | `info` blue | No |

**Modal overlay** (built as a RealDash **trigger → show/hide group** or a full-page indicator):

- `x80 y120 w640 h240`, background `alarm` red @ 92% opacity, centered white text.
- Trigger: `ST185: Low Oil Press 2` =1 **OR** `ST185: High Coolant Press` =1 → show; both 0 → hide.
- Text: the active fault name, 64 px bold; subtext "REDUCE LOAD / CHECK GAUGES" 28 px.
- Dismiss: auto-hides when the bit clears (latching is the ECU's job, not the display's).

---

## 10. Build steps in the RealDash editor

1. **Connect CAN.** Garage → open the door → tap the instrument cluster → Connections → add **CAN
   bus** connection on the USB-CAN adapter at **1 Mbit/s** (`bus 0`).
2. **Import inputs.** On that connection: **Select Vehicle → Custom Channel Description File →**
   browse to `link_g4x_realdash.xml`. Confirm the `ST185:` inputs appear under **Settings → Inputs →
   ECU Specific**. (If you re-import after edits, clear old imported values first under **Settings →
   Units & Values**.)
3. **New dashboard.** Create a blank dash, set background `#0A0C10`, landscape, and add **3 pages**.
4. **Top strip.** Build §5 once on page 1, then copy/paste the group onto pages 2 and 3 (or use a
   shared layer). Bind each indicator to its bit input; set on/off colors per §5.
5. **Page 1 / DRIVE.** Add the six tiles per §6. Use **Numerical** gauges for the index/value heroes,
   **Bar** gauges for Throttle and TC Intervention, **Text** gauges with *enum* for Cruise and A/C.
6. **Page 2 / SENSORS.** Add the 4 × 2 grid per §7. Use **Needle/Round** gauges for IAT, coolant
   pressure, turbo speed, fuel temp; **Bar** for engine load and ethanol; **Numerical** for cabin
   temp and trigger errors. Set each gauge's caution/alarm color bands to the thresholds in §7.
7. **Page 3 / G-FORCE.** Add bars + the g-ball per §8; wire the dot's two position animations.
8. **Alarms.** Add the modal overlay group and the trigger in §9.
9. **Theme pass.** Apply the §4 palette and typography to every gauge (Look'n'Feel → Colors / Font).
10. **Save** the `.rd`. Keep `link_g4x_realdash.xml` in this repo as the source of truth for inputs;
    the dashboard depends on the `ST185:` names existing.

---

## 11. Maintenance notes

- **Inputs are the contract.** If you rename a value in `link_g4x_realdash.xml`, every gauge bound to
  the old name breaks. Rename in the XML and re-bind, or keep names stable.
- **Thresholds are starting points.** IAT/coolant/turbo/fuel-temp bands above are sane defaults for a
  3S-GTE track car; tune them to your engine, turbo, and event once you have logged data.
- **No transmit.** RealDash is listen-only here — never add `writeInterval`/`initialValue` to these
  frames; the ECU owns 0x3EF–0x3F1 (see master-design §7 and Conflict B).
- **Bit map is canonical.** The 0x3F1 byte-6 warning bits follow `link_g4x_can_setup.json` /
  `CAN-BUS-ID-ALLOCATION-TABLE.md` §6. If those change, update the per-bit `<value>` entries to match.
