# RealDash Layout Design — ST185 TrackCluster

Buildable dashboard design for the **Raspberry Pi RealDash** secondary display on the 1993 Celica
GT-Four (5S-GTE) track build. This is the spec you build against in the RealDash visual editor; it
pairs 1:1 with the inputs in [`link_g4x_realdash.xml`](link_g4x_realdash.xml). A browser preview of
the finished look is [`realdash-simulation.html`](realdash-simulation.html) (open in any browser).

> **Why a spec and not a `.rd` file?** RealDash dashboards (`.rd`) are a binary format produced only
> by the in-app visual editor. The layout is version-controlled here as a buildable spec plus the
> importable channel-description XML it binds to.

> **CAN scope:** RealDash listens only to the three ECU->RealDash frames **0x3EF / 0x3F0 / 0x3F1**.
> The cluster frames 0x3E8-0x3EE (RPM, boost, temps, speed, gear, lambda, protection) belong to the
> **center cluster** and are documented in
> [`CANBUS-ENCODE-DECODE-REFERENCE.html`](CANBUS-ENCODE-DECODE-REFERENCE.html) — RealDash does not
> display those (no duplication).

---

## 1. Design principles

RealDash is the **secondary** display; the ESP32 center cluster shows the primary vitals. RealDash
surfaces what the cluster does **not**: driver-assist state, extended sensors, and the extended
warning bits.

- **Glanceable** — a value readable in < 0.5 s.
- **Single page** — one 800x480 engineering grid; no page swiping, no media player.
- **Color = state** — neutral OK; **amber** = caution; **red** = alarm; **blue** = active/informational.
- **No duplication** — anything already on the cluster is omitted on purpose.

---

## 2. Hardware & canvas

| Property | Value |
|---|---|
| Device | Raspberry Pi 4+/Pi 5 running RealDash |
| Screen | 7" panel, **800 x 480** landscape |
| CAN | USB-CAN adapter, **1 Mbit/s**, passive listener, BigEndian |
| Connection XML | `link_g4x_realdash.xml` (RealDash CAN v2) |
| Layout | **One page** + persistent top status strip |

---

## 3. Theme — blue + brushed chrome

Bright graphite base with electric-blue and brushed-chrome accents.

| Token | Hex | Use |
|---|---|---|
| `bg` | `#1a2430` | page background (graphite) |
| `panel` | `#243243` | tile background |
| `edge` | `#3c5066` | tile border |
| `blue` | `#34a8ff` | primary active accent |
| `cyan` | `#46e6ff` | secondary blue accent |
| `chrome` | `#f4f7fb -> #c3ccd8 -> #889aac` | brushed-chrome rails / trim / title |
| `text` | `#f3f8ff` | primary numerals |
| `dim` | `#9fb1c6` | labels / units |
| `caution` | `#ffc233` | amber caution |
| `alarm` | `#ff4d57` | red alarm |

---

## 4. Top status strip (persistent)

`x0 y0 w800 h54`, dark-blue bar with a chrome hairline. Left: `ST185 . DASH` title; a clock sits
bottom-right. Info chips glow solid; caution/alarm chips **strobe** (amber ~2 Hz, red ~3 Hz). There
is **no full-screen modal overlay** — a strobing strip chip is the alarm.

| Chip | Input | Color when active |
|---|---|---|
| `FLAT` | `ST185: Flat Shift` | blue (info) |
| `FAN` | `ST185: Radiator Fan` | blue (info) |
| `LOFUEL` | `ST185: Low Fuel` | amber, strobe |
| `SBFLT` | `ST185: Switchboard Fault` | amber, strobe |
| `COOLANT P` | `ST185: High Coolant Press` | red, strobe |
| `OIL P 2` | `ST185: Low Oil Press 2` | red, strobe |

---

## 5. Single page — 4 x 4 tile grid

Uniform 4-column grid. Each tile: uppercase label, big value, optional bottom progress bar that
turns amber/red at threshold; a 3px left accent stripe (chrome default, blue on active driver-assist
tiles). Cruise and A/C span two columns on the bottom row.

| # | Tile | Input | Range / display | OK | Caution | Alarm |
|---|---|---|---|---|---|---|
| 1 | Boost Map | `ST185: Boost Map` | index 0-3 (LOW/MID/HIGH/MAX) | — | — | — |
| 2 | TC + intervention | `ST185: TC Setting` / `TC Intervention` | 0-4 + % bar | <10% | 10-40% | >40% |
| 3 | Throttle | `ST185: Throttle` | 0-100 % + bar | any | — | — |
| 4 | Target lambda | `ST185: Target Lambda` | 0.60-1.30 lambda | any | — | — |
| 5 | Charge-Pipe IAT | `ST185: Charge-Pipe IAT` | 0-80 C + bar | <50 | 50-60 | >60 |
| 6 | Coolant Pressure | `ST185: Coolant Pressure` | kPa (u16) + bar | 50-150 | 150-200 | >200 or `High Coolant Press`=1 |
| 7 | Turbo Speed | `ST185: Turbo Speed` | 0-200,000 RPM + bar | <90% | 90-95% | >95% of turbo max |
| 8 | Engine Load | `ST185: Engine Load` | 0-100 % + bar | any | — | — |
| 9 | Fuel Temp | `ST185: Fuel Temp` | 0-90 C + bar | <55 | 55-70 | >70 |
| 10 | Ethanol | `ST185: Ethanol` | 0-100 % (E-blend) + bar | any | — | — |
| 11 | Lat G | `ST185: Accel Y` | lateral g (signed) | any | — | — |
| 12 | Trigger Errors | `ST185: Trigger Errors` | count | =0 (green) | 1-4 | >=5 (sync loss) |
| 13 | Cruise (spans 2) | `ST185: Cruise State` | enum OFF/STBY/SET/RES/OVR | OFF dim / SET-RES blue | OVR amber | — |
| 14 | A/C (spans 2) | `ST185: AC Status` | enum OFF/REQ/ON/FLT | ON blue | — | FLT red |

> **Coolant Pressure** is now a **u16** wire value (0x3F0 bytes 2-3), so it is no longer capped at
> 255 kPa. **Turbo Speed** is a single byte `raw x1000` -> 0-255,000 RPM (1,000 RPM resolution), covering an EFR's full spool range. **Cabin Temp was
> dropped** from 0x3F0 to make room for the u16 coolant pressure and is no longer a RealDash input
> (see `CAN-CONFIG-STATUS.md`); tile #11 uses the lateral accel input instead.

---

## 6. Input inventory (binds to `link_g4x_realdash.xml`)

Every gauge binds to a custom `ST185:` input under **Settings -> Inputs -> ECU Specific**.

| Input | Frame | Raw -> value | Unit |
|---|---|---|---|
| `ST185: Target Lambda` | 0x3EF | V x0.001 | lambda |
| `ST185: Throttle` | 0x3EF | V | % |
| `ST185: TC Setting` / `ST185: TC Intervention` | 0x3EF | index / V | — / % |
| `ST185: Boost Map` | 0x3EF | index 0-3 | — |
| `ST185: Cruise State` / `ST185: AC Status` | 0x3EF | enum | text |
| `ST185: Fuel Temp` / `ST185: Charge-Pipe IAT` | 0x3F0 | V-50 | C |
| `ST185: Engine Load` / `ST185: Ethanol` | 0x3F0 | V | % |
| `ST185: Coolant Pressure` | 0x3F0 | V (u16, bytes 2-3) | kPa |
| `ST185: Turbo Speed` | 0x3F0 | V x1000 | RPM |
| `ST185: Trigger Errors` | 0x3F0 | V | count |
| `ST185: Accel X/Y/Z` | 0x3F1 | V x0.1 (signed) | g |
| `ST185: Flat Shift` / `ST185: Radiator Fan` / `ST185: Low Fuel` / `ST185: High Coolant Press` / `ST185: Low Oil Press 2` / `ST185: Switchboard Fault` | 0x3F1 | byte6 bits 0-5 | 0/1 |

> **Cabin Temp is no longer a RealDash input** — dropped from 0x3F0 when Coolant Pressure was widened
> to u16. To restore it, add a new ECU frame (e.g. 0x3F2) with a matching RealDash value; do not
> point RealDash at the switchboard 0x640 frame.

---

## 7. Alarm logic

Priority high->low; all surface on the **strip** (no modal overlay):

| Priority | Condition | Chip | Color |
|---|---|---|---|
| 1 | `Low Oil Press 2` = 1 | OIL P 2 | red, strobe |
| 2 | `High Coolant Press` = 1 (or coolant >200 kPa) | COOLANT P | red, strobe |
| 3 | `Trigger Errors` >= 5 | Trigger Errors tile | red |
| 4 | `Switchboard Fault` = 1 | SBFLT | amber, strobe |
| 5 | `Low Fuel` = 1 | LOFUEL | amber, strobe |
| 6 | `Radiator Fan` / `Flat Shift` = 1 | FAN / FLAT | blue, solid |

Primary engine-protection alarms (knock, cuts, primary oil pressure, over-temp) stay on the
**cluster** (0x3EE). Cluster = engine protection; RealDash = assist + extended.

---

## 8. Build steps (RealDash editor)

1. **Connect CAN** on the USB-CAN adapter at **1 Mbit/s**.
2. **Import inputs:** Select Vehicle -> Custom Channel Description File -> `link_g4x_realdash.xml`;
   confirm the `ST185:` inputs appear under Settings -> Inputs -> ECU Specific.
3. **New dashboard,** background `#1a2430`, landscape, **one page**.
4. **Top strip** per section 4; bind each chip to its bit input; strobe the caution/alarm chips.
5. **4x4 grid** per section 5 — Numerical gauges for values, Bar gauges for progress bars, Text/enum
   for Cruise and A/C. Apply the section 3 theme and the section 5 bands.
6. **Save** the `.rd`. Keep `link_g4x_realdash.xml` as the source of truth for input names.

---

## 9. Maintenance notes

- **Inputs are the contract.** Renaming a value in `link_g4x_realdash.xml` breaks every bound gauge.
- **Thresholds are starting points** — tune to your engine, turbo, and event.
- **No transmit.** RealDash is listen-only; never add write intervals to 0x3EF-0x3F1.
- **Bit map is canonical** — the 0x3F1 byte-6 warning bits follow `link_g4x_can_setup.json` /
  `CAN-BUS-ID-ALLOCATION-TABLE.md`.
