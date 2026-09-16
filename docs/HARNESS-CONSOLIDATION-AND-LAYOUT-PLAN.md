# Harness docs consolidation + layout plan — 2026-09-12

Proposal only for *where files should live* and *how the two `.harness` drawings should be laid out*. Pin assignments in this note match the 2026-09-12 OEM-block / BRZ-pedal pass; do not treat dated audit notes as living pin maps.

## 1. What is redundant today

Several surfaces describe the same ECU pin story. They drifted before; they will drift again if all of them stay “living.”

| Surface | Job it is actually good at | Overlaps | Keep as |
|---|---|---|---|
| `XTREMEX-IO-TABLE.html` | Channel + Superseal pin + colour + function | Everything below copies it | **Living pin SoT** |
| `docs/XTREMEX-IO-VERIFY-2026-09-11.md` | Dated pin-vs-QSG record | Repeats the table | **Frozen record** — do not update except to close a listed gap |
| `docs/ECU-IO-AUDIT-2026-09-12.md` | Dated cross-check of docs vs `.harness` | Repeats the table | **Frozen record** |
| `SCHEMATIC-WIRING.html` | One-page print/SVG of ECU I/O | Same nets as the interactive app | **Print face** of the schematic app. No new pin inventions here |
| `apps/harness-schematic/index.html` | Interactive loom/schematic | Same nets as the SVG + `.harness` | **Living schematic face** |
| `docs/harness/HARNESS_WIRING_DIAGRAM.html` | Redirect stub | None | Keep as pointer |
| `docs/harness/ST185-Power.harness` | Power BOM, splices, layout | Duplicates sensors that belong in Signal | **Living power SoT** |
| `docs/harness/ST185-Signal.harness` | Signal BOM, ECU A/B/C, layout | Duplicates power-only parts (`rad_fan`, `fan2`, `buck`, `fuelpump`, `mrs_pwr`) | **Living signal SoT** |
| Desktop `Documents\Wire Harnesses\…ECU Harness.harness` | Local harness.design copy | Third copy of the same looms | **Mirror** — pull from repo, do not edit as SoT |
| `DOCS-CLEANUP-PLAN.md` **and** `.html` | 2026-08-31 inventory (same content, two formats) | Each other; also stale (claims IO table unpushed, 3S-GTE, FuryX) | **Done 2026-09-16** - both now in `archive/`; the MD carries a superseded banner |
| `CANBUS-ENCODE-DECODE-REFERENCE.html` (this repo) | Byte-identical copy of the cluster file | `center-cluster-esp32-p4` original | Keep a copy for offline reading; **do not edit** — cluster `canbus.c` wins |
| `WIRING.md` | Cluster GPIO + 5-node CAN physical | `CAN-BUS-MASTER-DESIGN.md` topology paragraphs | Keep; strip any ECU-cavity claims (already defers) |
| `docs/HARNESS-FACES-2026-09-11.md` | Why schematic ≠ `.harness` | This plan | Fold the “two faces” rule into this file, then leave the dated note frozen |
| `docs/BOARD-VERIFY-2026-09-11.md` | Claude board vs git | Unrelated to harness pins | Frozen |

**Do not create** a third APS/ETB markdown (`DBW-ETB-AND-PEDAL.md` was proposed in the cleanup plan and never written). The 6-pin BRZ pedal lives in the IO table + both `.harness` files.

## 2. Consolidation plan (do in this order)

1. **Crown one living pin map.** `XTREMEX-IO-TABLE.html` is it. Schematic app, SVG schematic, and `.harness` files are *faces* of that table, not peers.
2. **Crown two living harness files.** Repo `docs/harness/ST185-Power.harness` and `ST185-Signal.harness`. The desktop copy is a checkout, not a third original.
3. ~~**Stop dual-maintaining the cleanup plan.**~~ **Done 2026-09-16.** Both `DOCS-CLEANUP-PLAN.html` and `.md` now live in `archive/`; the markdown carries a superseded banner pointing here. Its section 12 open decisions were closed out at Daniel's direction, not carried forward.
4. **Keep dated verify/audit notes frozen.** New pin facts go into the IO table first, then the two faces. Do not append living pin maps onto `VERIFY` / `AUDIT` / `FACES` notes.
5. **Print schematic.** Either export from the interactive app when it can, or treat `SCHEMATIC-WIRING.html` as a hand-drawn one-pager that *only* changes when the IO table does. No connector PNs, no AWG, no bundle lengths there.
6. **Cluster CAN HTML.** Leave the duplicate `CANBUS-ENCODE-DECODE-REFERENCE.html` until a dedicated CAN-docs pass; it is not a harness problem.

Nothing in this list requires a CAN ID or cluster-firmware change.

## 3. Drawing convention — OEM “block”

Anything that is an OEM body/engine-bay connection is a **generic block**: only the wires *our* harness lands, no invented OEM internals.

| Draw as a generic OEM block | Draw with a real pinout |
|---|---|
| Relays (EFI, ETB, FP, fans, start) | Link Superseal A / B / comms |
| Firewall bulkheads A and B | BRZ e-throttle pedal (6-pin Sumitomo TS 025) |
| Clutch, brake, reverse, start | Aftermarket sensors we specify (MAP, Bosch ETB, Continental flex, NCV1124, …) |
| Cruise control stalk (ladder + MAIN/SET/RESUME as **one** block) | CSB3 screw terminals (until a real I/O housing is chosen) |
| Ignition switch (dummy block → DI 9) | |
| AC amplifier | |

Bulkheads stay 2-cavity TBD blocks until a wire actually terminates in a cavity. Do not put a 37-way 8STA pinout on the drawing “for later.”

## 4. Better layout for Power vs Signal

### 4.1 What each file owns

**Power** (`ST185-Power.harness`) — battery, fuses, OEM relay blocks, switched 12 V, +5 V / +8 V / Gnd Out splices, high-current loads, BRZ pedal **supplies** (pins 1, 2, 4, 5).

**Signal** (`ST185-Signal.harness`) — ECU A/B/C, every sensor/DI/aux wire, CAN, CSB3 I/O, OEM switch blocks, BRZ pedal **VPA1/VPA2** (pins 6 and 3), ignition-switch sense to DI 9.

A part may appear in both files only when it has both a power pin and a signal pin (BRZ pedal, ETB, flex, COPs). Power-only parts must not remain in Signal (`rad_fan`, `fan2`, `buck`, `fuelpump`, `mrs_pwr` — delete on the next layout pass).

### 4.2 Column order (both views, 30 px grid)

Same story left-to-right in schematic and layout, wide rather than a tall ribbon.

**Power**

1. SOURCE (battery / chassis)
2. DISTRIBUTION SPLICES (`sp_12v`, `sp_sw12`, `sp_5v`, `sp_8v`, `sp_gndout`)
3. OEM RELAY BLOCKS + dummy ignition-switch block
4. CABIN loads (buck, CSB3 power, BRZ pedal supplies)
5. ENGINE loads (injectors, COPs, fans, pump)
6. ENGINE sensors that take 5 V / 12 V / Gnd Out only

**Signal**

1. ECU-A / ECU-B / ECU-Comms (stacked, real Superseal footprints)
2. Aftermarket engine sensors (crank, cam, MAP, pressures, knock, flex, WSS + VR)
3. DBW (Bosch ETB signal pins, BRZ 6-pin pedal)
4. OEM BODY BLOCKS (ignition switch, start, clutch, cruise stalk, brake, reverse, AC amp)
5. OEM BULKHEAD BLOCKS (pass-through, no fake pin schedule)
6. CAN nodes (lambda, CSB3, cluster headers)

Vertical pitch = `60 + 30 × cavities`, 60 px between parts, 180 px between columns. Wrap a column rather than exceeding ~2400 px height.

### 4.3 Ignition switch / Hold Power

Dummy OEM block **Ignition Switch**:

- Signal file: `IGN ON` → ECU **DI 9 / B28** (green). PCLink function: Ignition Switch, used with Aux 6 hold.
- Power file: same block present for layout/BOM; sense wire is not duplicated there.
- Do not invent ACC / IG1 / ST internals. Start remains a separate OEM start-request block on DI 7.

### 4.4 BRZ pedal (both files)

Looking into the 6-way, locking tab at top:

| Pin | Name | Power file | Signal file |
|---|---|---|---|
| 1 | VC2 +5 V (sub) | to `sp_5v` | NC |
| 2 | GND2 | to `sp_gndout` | NC |
| 3 | VPA2 APS-S | NC | An Volt 5 **B33** |
| 4 | VC1 +5 V (main) | to `sp_5v` | NC |
| 5 | GND1 | to `sp_gndout` | NC |
| 6 | VPA1 APS-M | NC | An Volt 4 **A14** |

Main = full-range track. After probing, set PCLink `APS (Sub) 100%` if the sub track saturates early.

### 4.5 Next layout pass (not done in this change)

- Delete the five power-only duplicates from Signal.
- Land bulkhead cavities only when a wire actually crosses the firewall — then the block gains real designations, still without claiming an 8STA PN until that connector is bought.
- ~~Generate a `HARNESS-BUILD-LIST` from the schematic graph.~~ **Done 2026-09-16.** `docs/harness/buildlist.py` generates `docs/harness/HARNESS-BUILD-LIST.csv` (242 wires) from all three `.harness` files: From / To / pin / signal / crimp terminal / colour / AWG / trunk route / est mm / splice / done. Regenerate after any harness change - do not hand-edit the CSV.
- Two gaps the build list exposes, both real data gaps and neither guessed at: **no wire gauge exists anywhere in the `.harness` files**, so the AWG column ships blank and needs a sizing pass; and **57 connectors have no contact part linked** to their `connectorPart`, so their crimp terminal PN is blank (the DEUTSCH bulkheads and both ECU shells are the biggest offenders).
- **Bulkhead C is not attached to the bundle/trunk graph** - 9 of its wires route nowhere. Land it in the trunk layout on the next pass.

## 5. Already applied in this pass

- DI 9 ← dummy OEM ignition-switch block.
- Relays, bulkheads, clutch, cruise stalk, brake, reverse, start, AC amp labelled as OEM blocks.
- Cruise MAIN/SET/RESUME + ladder collapsed to **one** stalk block in the Signal file and the schematic app.
- BRZ 6-pin APS in Power, Signal, IO table, SVG schematic, and the interactive app.

## 6. Build rules — set by Daniel, 2026-09-16

These govern the rework. Where they conflict with anything above, these win.

### 6.1 Harness split

Three harnesses. **Only two bulkhead connectors exist.**

| Harness | Crosses | Carries |
|---|---|---|
| **A / B** (engine + signal) | Bulkheads A and B, **passenger side** | Everything ECU-side. All IAT sensors live here. |
| **C — Engine Room Harness** | **No bulkhead.** Exits the driver fender, around the front of the bay | Radiator fan, condenser fan, EPS pump, headlights + headlight motors, turn, horn, wipers, washer pump, and any power for devices not already on A/B |

`bh_c` is deleted. Its rad fan, condenser fan and MRS pump loads move to the Engine Room
Harness. **Nothing else comes off A/B except the EPS pump.**

Acceptance test for the split: pull the engine, unplug two connectors, the engine loom
comes with it.

### 6.2 Power distribution — PDM or relay+fuse, never both

- A load is fed **either** from a PDM output **or** from a relay and fuse. Not both.
- Any load exceeding the PDM's per-output capacity gets a relay and fuse instead.
- Where a load exceeds one output but the PDM is still the right source, **combine
  outputs** (the fuel pump is the likely case). Check the PDM's per-output cap before
  assigning.
- Relays appear **only in the power harness**, with every wire routed to its real
  destination. No placeholders, no bare "ground" stubs standing in for a path.
- Relay coil polarity follows the ECU's drive type (active low vs active high) per the
  Link manual, or the terminal's capability.

### 6.3 Bulkhead pin priority — revised

Supersedes the earlier "power and ground take precedence over shields" rule.

1. **Every shield gets its own bulkhead pin.** Shields are allocated first.
2. **Sensor 5V and sensor ground are spliced at the bulkhead connector**, not at the ECU.
   Saves pins and keeps the ECU-side harness smaller.

Current headroom: bulkhead A is 47 cavities with 32 used, B is 21 with 10 used — 26 spare
against roughly 18-19 engine-side shields. It fits, but the spare breakout and the new
device connectors will eat into that. Recount before committing the layout.

**Open:** whether shields for timing- and fuelling-critical sensors (crank, cam, knock)
stay individually unspliced, or are grouped by signal type. Not yet decided.

### 6.4 Shields

- Drawn as a dotted oblong at the connector/device end, described **"drain"**.
- Terminated **only** at the ECU shield-ground end. Floating at the device end, always.
- Carried through the bulkhead and continued to the ECU connector shield ground.
- Kept separate rather than spliced, ideally until just before the ECU connector.

### 6.5 Grounds

- Sensor grounds go to **Gnd Out**. ECU ground goes to **battery negative**.
- Sensors never land on chassis ground or battery ground — coils excepted (and possibly
  injectors, to confirm).

### 6.6 Wire and contact selection

- **Gauge:** sized on typical peak amps for the **high-performance** version of the device
  (size the fan circuit off a high-output fan's real draw, not the OEM unit), plus margin,
  and constrained by the available contact sizes where the circuit crosses a bulkhead.
- **Wire:** high-temp — Tefzel, TXL, or mil-spec equivalent.
- **Contacts:** gold, barrel where available, sized to peak current and temperature.
- Don't forget backshells, strain relief, sealing and rubber boots, wire seals, wedge
  locks, Raychem, junction boots, heat shrink, and shielded cable where specified.

### 6.7 Connectors

- Every connector is **named for the device it connects to**.
- No wire runs direct to a device. Anything currently drawn that way gets a connector:
  look up the real one, invent a generic part number with correct pins and assignments, or
  use a Deutsch connector for PCB-type hardware (ECUMaster switchboard, CAN transceivers,
  the two dual-channel ABS sensor conditioner boards).
- Cam sensor is **8V** and needs a connector; the pull-up resistor was already specified in
  an earlier session. The boost control solenoid needs a connector too.
- Nothing downstream of the CAN transceiver — no cluster parts.
- Spare breakout to be added while the design is still on paper: spare Aux, spare An Volt,
  spare power, and the PDM's unused outputs.

### 6.8 Resistors

Only where physically required — not where the ECU already provides the pull-up or
pull-down internally. Any that are required must be drawn with a complete path and listed
on the master BOM.

### 6.9 Layout

Orthogonal on a 30px grid. Diagonals only where a part fan-out makes them unavoidable.

### 6.10 Known fault to fix

ETB cavity c3 (+5V TPS supply) currently has two wires on it: the engine-side 5V splice
(correct) and `w_hv_etb` from the ETB Power Relay through bulkhead C, which carries
switched **12V**. That is a 12V-to-5V short that would take out both TPS tracks and likely
the ECU's 5V regulator. A Bosch DBW throttle body has no power input — the relay's job is
feeding the ECU's V-Ethrottle pin, which `w81`/`w82` already do. **Delete `w_hv_etb_c` and
`w_hv_etb_e`.** Motor +/− stay on bulkhead B, TPS signals stay on bulkhead A.
