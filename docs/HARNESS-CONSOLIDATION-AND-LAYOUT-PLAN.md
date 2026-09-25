# Harness docs consolidation + layout plan — 2026-09-12

Proposal only for *where files should live* and *how the two `.harness` drawings should be laid out*. Pin assignments in this note match the 2026-09-12 OEM-block / BRZ-pedal pass; do not treat dated audit notes as living pin maps.

> ## READ THIS FIRST — the document contradicts itself on purpose
>
> **2026-09-25:** the pin SoT is `sot/channels.csv`. The retired diagrams and
> dated audit notes named in the section 1 table were moved to
> `archive/2026-09-25-cleanup/`. The looms are `docs/harness/rebuild/*.harness`.
>
> This file grew by accretion. **Sections 1–5 describe the world of 2026-09-12**,
> when there were two living harness files, `ST185-Power.harness` and
> `ST185-Signal.harness`. That is no longer the structure.
>
> **Where sections 1–5 and section 6.x disagree, 6.x wins, and the highest
> numbered subsection wins within 6.x.** The current loom structure is defined in
> **6.41**, not in section 2.
>
> | Then (sections 1–5) | Now (6.41) |
> |---|---|
> | 2 living looms: Power, Signal | 6 looms: A, B, C, CAN, cabin accessory, rear trunk |
> | Split by power vs signal | Split by which bulkhead a wire crosses |
> | `docs/harness/*.harness` | `docs/harness/rebuild/*.harness` |
>
> Sections 1–5 are kept because the reasoning in them — one living pin map, faces
> not peers, frozen dated notes, the OEM-block drawing convention in section 3 —
> is still binding. Only the two-file loom split is superseded.
>
> **Which harness file is current: `docs/harness/README.md`.**

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
| `docs/harness/ST185-Power.harness` | Power BOM, splices, layout | Duplicates sensors that belong in Signal; leftover `bh_c` still drawn | **Living power SoT** (ECU 12 V / relays). Do not build `bh_c` |
| `docs/harness/ST185-Signal.harness` | Signal BOM, ECU A/B/C, layout | Duplicates power-only parts (`rad_fan`, `fan2`, `buck`, `fuelpump`, `mrs_pwr`) | **Living signal SoT** |
| `docs/harness/ST185-EngineRoom-C.harness` | Partial engine-room add-on + OEM J/B injection | Overlaps Power leftover `bh_c` fan/EPS 87 wires | **Living engine-room C SoT** |
| `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` | Kick-panel / J/B2 splice table + EWD snips | None as a table | **Living splice table** |
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
- ~~Generate a `HARNESS-BUILD-LIST` from the schematic graph.~~ **Done 2026-09-16.** `docs/harness/buildlist.py` generates `docs/harness/HARNESS-BUILD-LIST.csv` from Signal, Power, CAN and EngineRoom-C. From / To / pin / signal / crimp terminal / colour / AWG / trunk route / est mm / splice / done. Regenerate after any harness change - do not hand-edit the CSV.
- Two gaps the build list exposes, both real data gaps and neither guessed at: **no wire gauge exists anywhere in the `.harness` files**, so the AWG column ships blank and needs a sizing pass; and **57 connectors have no contact part linked** to their `connectorPart`, so their crimp terminal PN is blank (the DEUTSCH bulkheads and both ECU shells are the biggest offenders).
- ~~**Bulkhead C is not attached to the bundle/trunk graph.**~~ **Superseded 2026-09-17.** `bh_c` is deleted. Engine-room add-on wiring is `docs/harness/ST185-EngineRoom-C.harness`; OEM power restoration is the splice table in `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md`.

## 5. Already applied in this pass

- DI 9 ← dummy OEM ignition-switch block.
- Relays, bulkheads, clutch, cruise stalk, brake, reverse, start, AC amp labelled as OEM blocks.
- Cruise MAIN/SET/RESUME + ladder collapsed to **one** stalk block in the Signal file and the schematic app.
- BRZ 6-pin APS in Power, Signal, IO table, SVG schematic, and the interactive app.

## 6. Build rules — set by Daniel, 2026-09-16

These govern the rework. Where they conflict with anything above, these win.

### 6.1 Harness split

Three harnesses. **Only two signal bulkheads exist** (HDP20 A and B, passenger side).
Large DC uses RADLOK, not a third HDP20. `bh_c` is deleted.

| Harness | Crosses | Carries |
|---|---|---|
| **A / B** (engine + signal) | Bulkheads A and B, **passenger side** | Everything ECU-side. All IAT sensors. A/C compressor clutch. EPS *speed* and *relay-request* only. |
| **C — Engine Room Harness (partial)** | **No HDP20.** OEM engine-room / cowl / dash looms stay. Add-on wires only | Uprated rad + condenser fan power, EPS *power/ground/enable* up the passenger fender in the vacated ABS actuator trough, J/B2 dummy-header feeds, kick-panel B+ / AM1 / AM2 injection. Headlights, turn, park, horn, wipers, washer stay on the OEM engine-room loom — we only restore their power. |
| **Heavy DC** | RADLOK 5.7 mm +/− at the firewall | Trunk battery → glove-box PDB → starter B+ / 160 A alt. Jump lugs at trunk, PDB, starter, block. |

Battery is in the **trunk**. Fuse block, PDB, PMU-16 and the relays the PMU cannot replace sit in the **passenger glove box** (next to OEM R/B No.3 / No.4). Kick-panel J/B No.1, R/B No.2 / No.3 / No.4 stay — do not clone them.

**Nothing else comes off A/B except the EPS control wires.** ABS solenoid, 60A FL ABS and crash sensors are deleted.

Acceptance test for the engine split: pull the engine, unplug bulkheads A and B, the engine loom comes with it. Engine-room C and the OEM body loom stay in the car.

Splice table, factory citations and the C drawing: `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md`, `docs/harness/ST185-EngineRoom-C.harness`.

### 6.2 Power distribution — per load, PDM or relay+fuse, never both

**The rule is per load, not per car.** A mixed system is expected and correct: the PMU
feeds what fits, relays feed what does not. What is forbidden is putting a *single* load
behind both a PMU output and a relay.

- A load is fed **either** from a PDM output **or** from a relay and fuse. Not both.
- Any load exceeding the PDM's per-output capacity gets a relay and fuse instead.
- Where a load exceeds one output but the PDM is still the right source, **combine
  outputs** (the fuel pump is the likely case). Check the PDM's per-output cap before
  assigning.
- Relays appear **only in the power harness**, with every wire routed to its real
  destination. No placeholders, no bare "ground" stubs standing in for a path.
- Relay coil polarity follows the ECU's drive type (active low vs active high) per the
  Link manual, or the terminal's capability.

#### 6.2.1 PMU-16 scope — settled by Daniel, 2026-09-17

**ECUMaster PMU-16, in the passenger glove box.** Verified spec: 10 × 25 A continuous,
6 × 15 A continuous, 150 A total, outputs may be paralleled (max three → 75 A),
2 × CAN 2.0 to 1 Mbit, 16 analog inputs, 5 V / 500 mA sensor supply, and one dedicated
output with wiper braking. Source: ecumaster.com/products/pmu/.

The PMU carries **body, lighting and the small engine accessories**. Four loads stay on
relay + fuse because they do not fit a 25 A channel:

| Load | Draw | Source |
|---|---|---|
| EPS pump (MR-S EHPS) | 60–80 A peak | Relay `k_eps`, HCR 150 / F7 60 A |
| Radiator fan (uprated) | 20–25 A run, 40–60 A inrush | Relay `k_fan` |
| Condenser fan | 10–15 A run, 30–40 A inrush | Relay `k_fan2` |
| Fuel pump (450 lph, E85) | ~22–25 A at pressure | Relay `k_fp` |

Everything else that draws under ~15 A goes on a PMU channel: headlights and pop-up
motors, turn / hazard, horn, wipers (use the braking output), washer, dome, rear defog,
accessories, plus ECU main, O2 heater, boost solenoid and purge.

Rejected: putting the PMU on engine / high-current loads. It would burn three or four
paralleled channels per load, still could not take the EPS pump, would leave ten channels
idle, and would put the engine behind one device that cannot be swapped trackside.

The PMU is a **CAN 1** node at 1 Mbit/s. Add it to `WIRING.md` and
`CAN-BUS-MASTER-DESIGN.md` in the same change that lands it on the car, and do **not**
add a third 120 Ω terminator.

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

**Gauge sizing basis — settled by Daniel, 2026-09-17.** Applies to all 275 wires; none
currently carries a gauge.

1. Start from the **peak** current of the **high-performance version** of the device, not
   the OEM part's rating.
2. Add margin for **error, high ambient temperature and voltage drop**. Engine-bay runs
   and long runs get more.
3. **The wire is sized first. The contact is then chosen to fit the wire** — never the
   reverse.
4. A wire must **not exceed the maximum AWG its connector's contacts accept**. If the
   required wire is too big for the contact, change the contact or the connector; do not
   thin the wire.
5. When two sizes are defensible, **take the larger one**. Size for caution.
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

### 6.11 Which file a wire belongs in — supersedes §4.1

§4.1 split the files by "power vs signal hardware". That is replaced by a pin-level rule.

**Default: every ECU pin is Signal.** Two carve-outs go to Power.

| Goes in **Signal** | Goes in **Power** |
|---|---|
| Every ECU pin, by default | ECU **12V ignition supply**, with its power-hold wiring |
| **All** pedal (APS) pins — supplies included | **All relay trigger outputs** (the ECU wires that drive relay coils) |
| **All** ETB pins — motor +/− included | Relays, fuses, battery feed, grounds |
| **All** 5V sensor power, and the 5V splices | 12V circuits not named on the left |
| Sensors, CAN, injector and coil **drive** wires | Injector and coil **12V feeds** |

The relay-trigger carve-out is deliberate: it keeps each relay circuit whole in one drawing,
per §6.2 ("relays appear only in the power harness, with every wire routed to its real
destination").

A part legitimately appears in **both** files when it has both a power pin and a signal pin
(injectors, COPs, the MRS pump's control connector). That is not duplication.

Consequences for the current files:

- `sp_5v` and `sp_5v_eng` move to Signal.
- ETB leaves Power entirely, motor pair included — which makes the earlier "which bulkhead
  does ETB power cross" question moot.
- The BRZ pedal supply pins (VC1, VC2, GND1, GND2) move to Signal. This clears the
  `validate_harness` warnings about those cavities being flagged `notConnected` while
  carrying signal text — the contradiction only existed because the pins sat in Power.
- `k_fan` and `k_fan2` become Power-only.

### 6.12 Shields — how to model a floating shield without validation errors

The app supports a one-end shield natively. From its editing guide: a cable's `shield` core
"may connect at only one end (omit `target`)", using `color: "Shield"`.

So each shielded run is modelled as a **cable**, not as loose wires:

- `cores` — the signal conductors.
- `shield` — `source` set to the **ECU connector's shell** cavity, and **no `target`**. That
  is a genuinely floating shield at the device end.

A connector's `shell` field is the shield/backshell termination point, and the part invariant
is: a connector has a `shell` **iff** its part's `hasShell` is true.

Therefore the device-end connectors carry **no shell** — nothing is terminated there. Only
the ECU has one. This is the fix for the `part_mismatch` warnings on crank, knock, cam and
the four wheel-speed connectors: remove the shell from those connectors rather than adding
`hasShell` to their parts.

Note to check when converting: cables are schematic-only nodes in this app. Confirm the
layout view still routes the cores through bundles as expected before converting all of them.


### 6.13 File split - cut at the firewall, settled by Daniel 2026-09-17

harness.design caps a document at **100 connections**. Signal (112) and Power (114) both
exceed it, which makes them read-only in the app. The fix is to split each loom at the
bulkhead:

| Loom | Files | Holds |
|---|---|---|
| **A - sensor / signal** | `ST185-Signal-cabin.harness`<br>`ST185-Signal-engine.harness` | cut at bulkheads A and B |
| **B - power** | `ST185-Power-cabin.harness`<br>`ST185-Power-engine.harness` | cut at bulkheads A and B. **The MR-S EPS pump belongs to this loom.** |
| CAN | `ST185-CAN.harness` | 16 wires, unchanged |
| Engine room C | `ST185-EngineRoom-C.harness` | 33 wires, unchanged |

Each new file lands near 56 connections, leaving room for shields, the spare breakout and
new connectors before the cap bites again.

**The cut is already marked in the data.** Every firewall-crossing wire is drawn as a
`_c` / `_e` pair - `w12_c` runs `ecu_a` to `bh_a_fw`, `w12_e` runs `bh_a_eng` to `knock1`.
The cabin file takes the `_fw` halves, the engine file takes the `_eng` halves, and both
bulkheads appear in both drawings as the interface.

**Do not split by bulkhead A vs B.** It does not partition: `ecu_b` has wires through
bulkhead A (`w54_c`), and the engine-side splices `sp_gndout_eng`, `sp_5v_eng`,
`sp_sw12_eng` and `sp_cop_eng` each feed devices behind both bulkheads. That split would
duplicate shared nodes across files, which is how copies drift apart.

**One wire currently skips the firewall entirely:** `w_mrs_relay_req` runs from
`mrs_ctrl` (engine bay) straight to `k_eps`, which the Power and Signal files draw on the
cabin side while `ST185-EngineRoom-C.harness` draws it in the engine bay. With `k_eps`
settled as **engine bay** (see the EPS section of `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`)
that wire becomes engine-to-engine, and the relay's coil feed from `sp_sw12` becomes the
crossing that needs a bulkhead B pin.


### 6.14 File structure - revised by Daniel 2026-09-17, supersedes the table in 6.13

Loom **A** is the sensor / signal loom. Loom **B** is the power loom. Each is cut at the
firewall into an ECU-side and an engine-side drawing. The wheel-speed sensors come out of
both into a loom of their own.

| File | Holds |
|---|---|
| `ST185-A-ECU.harness` | Loom A, ECU side of bulkheads A and B |
| `ST185-A-engine.harness` | Loom A, engine side |
| `ST185-B-ECU.harness` | Loom B, ECU side. **All relays live here.** MR-S EPS pump is loom B |
| `ST185-B-engine.harness` | Loom B, engine side |
| `ST185-WheelSpeed.harness` | **New.** All four VR wheel-speed sensors and both conditioner boards. **No bulkhead connector** - this loom does not cross A or B |
| `ST185-EngineRoom-C.harness` | Loom C. 33 wires, fits one file; split it only if it outgrows the cap |
| `ST185-CAN.harness` | 16 wires, unchanged |

Do not split by "cabin vs engine" as a two-file scheme - that was the 6.13 proposal and it
is replaced by the four files above.

### 6.15 Shared parts across drawings - set by Daniel 2026-09-17

A part must appear on **exactly one** harness BOM. Otherwise the global buy list
double-counts it and we order twice.

**The rule.** A shared part is drawn in full, with its real part number, on the **one**
harness that owns it. Relays are owned by the **power loom (B)**. On every other drawing
the wire runs instead to a **dummy connection block** labelled with the component ID and
the pin it lands on - and that dummy block carries **no part number and no contacts**, so
it contributes nothing to that drawing's BOM.

```
Owning drawing (B-ECU)            Other drawing (A-ECU)
  ┌──────────────┐                  ┌──────────────────┐
  │ K4  Rad Fan  │                  │  K4-85           │   dummy block
  │ 6-1419137-4  │   ◄── same net ──│  (no part, no    │
  │ 85 86 30 87  │                  │   contacts)      │
  └──────────────┘                  └──────────────────┘
```

Apply the same pattern to **any** part shared between drawings - bulkheads, the fuse block,
the PDB, the PMU-16, splices - not only relays.

**Component IDs.** Every shared component carries a stable ID printed on every drawing it
appears on, so a wire can be traced across sheets by eye.

| ID | Internal id | Component | Owned by |
|---|---|---|---|
| `K1` | `k_efi` | EFI Main relay | B |
| `K2` | `k_etb` | E-throttle power relay | B |
| `K3` | `k_fp` | Fuel pump relay | B |
| `K4` | `k_fan` | Radiator fan relay | B |
| `K5` | `k_fan2` | Condenser fan relay | B |
| `K6` | `k_str` | Start relay | B |
| `K7` | `k_eps` | EPS pump relay (HCR 150) | B, engine side |
| `BH-A` | `bh_a_fw` / `bh_a_eng` | Bulkhead A, 47-way | A |
| `BH-B` | `bh_b_fw` / `bh_b_eng` | Bulkhead B, 21-way | A |
| `FB1` | `fusebox` | Cabin fuse block | B |
| `PDB1` | *(to add)* | Glove-box power distribution block | B |
| `PMU1` | *(to add)* | ECUMaster PMU-16 | B |

A dummy block is labelled `<ID>-<pin>`, e.g. `K4-85`, `BH-A-12`, `FB1-3`.

### 6.16 EPS pump relay is ECU-driven - settled by Daniel 2026-09-17

The pump runs only while the engine runs, so the ECU switches it rather than plain
ignition-switched 12 V.

- Coil high side: switched 12 V, as now.
- Coil low side: **Ign 6 / pin B12**, violet, low-side drive. Recorded "Available" in
  `XTREMEX-IO-TABLE.html`, freed 2026-09-06. Ign 5 / B13 already drives the condenser-fan
  relay, so the two relay triggers sit adjacent.
- **Delete `w_mrs_relay_req`** (`mrs_ctrl` to `k_eps`). The pump does not switch its own
  relay; that wire was a copy of the factory-reference drawing and is wrong for this build.
- Per 6.11 the trigger is a relay output, so it lives in the **power loom (B)**.


### 6.17 EPS moves entirely to loom C - settled by Daniel 2026-09-17

**Every EPS wire lives on loom C.** That includes the 60 A feed, the relay coil feed, the
relay `K7` itself and all three pump connectors. Loom B keeps none of it.

Consequences, all good:

- The two crossings 6.16 created - `w_fb_k_eps_30` and `w_k_eps_86` - disappear. Loom B no
  longer reaches the EPS at all.
- Bulkhead B gets **two pins back**: `c13` and `c14`, previously the pump speed and enable
  wires. Bank them against the shield allocation in 6.3.
- Loom C already runs EPS power up the passenger fender, so the relay now sits on a feed
  that was going there anyway.

**Open:** two EPS wires still start at the ECU - the `Ign 6 / B12` relay trigger and the
`Aux 7 / A27` speed pulse. Loom C has no bulkhead, so how they reach it is not yet decided.
Do not draw them until it is.

### 6.18 Starter trigger goes with the heavy DC - settled by Daniel 2026-09-17

`w_strl` (start relay `K6` to the starter solenoid) gets no bulkhead pin. It routes with
the heavy DC run and lands at the distribution block.

### 6.19 Glove-box distribution block `PDB1` - sourced 2026-09-17

Replaces the `PDB-M8x8 / TBD` placeholder in the buy list. Two verified candidates, both
tin-plated copper bus on UL 94-V0 glass-reinforced thermoplastic, both rated 300 V AC /
48 V DC, both with a matching insulating cover - which the glove-box location needs.

| | Blue Sea **2127** MaxiBus | Blue Sea **2104** PowerBar |
|---|---|---|
| Continuous | 250 A | **600 A DC** (545 A AC) |
| Studs | four 5/16"-18 | four 3/8"-16 |
| Stud torque | 132 in-lb (14.9 N·m) | see drawing |
| Max operating temp | 130 C | - |
| Insulating cover | **2719** | **2708** |
| Suits | 2 AWG lugs | 2 AWG through 1/0 lugs |

Source: bluesea.com product pages for 2127, 2104, 2719 and 2708.

**Which one depends on a question 6.1 has not answered:** does starter cranking current
pass *through* `PDB1`? 6.1 says "trunk battery -> glove-box PDB -> starter B+", which reads
as yes. Cranking is 200-400 A for a few seconds, so 250 A continuous would survive it but
with no margin. If the starter instead taps the main battery cable directly and `PDB1` only
feeds the fuse block, PMU-16 and accessories, 250 A is generous.

- Starter current through the block -> **2104 + 2708**.
- Starter fed off the main cable, block for accessories -> **2127 + 2719**.

Four studs either way. Current draw on `PDB1`: battery in, fuse block out, PMU-16 in
(150 A ANL), heavy DC to the engine bay, plus the jump lug - so four studs is the minimum,
and doubling lugs on a stud is acceptable within its torque spec.


### 6.20 Starter and alternator feeds - verified against the 1990 OEM EWD 2026-09-17

Read from `docs/electrical/ewd-snips/1990-st185-starting.png` (page 48) and
`1990-st185-charging.png` (page 52).

**What the factory actually does:**

```
BATTERY + ──┬── heavy black, NO fuse, NO fusible link ──► STARTER terminal B
            │
            └── FL MAIN 2.0L ──► F11 FUSIBLE LINK BOX
                                   ├─ 100A FL ALT ──► Alternator B
                                   ├─ 40A  FL AM1 ──► Ignition sw AM1
                                   └─ 30A  FL AM2 ──► Ignition sw AM2
```

Two corrections fall out of this.

**1. The starter lead is unfused in OEM - and we must not copy that.** The factory gets
away with it because the battery sits in the engine bay and the cable is about two feet
long. Our battery is in the **trunk**, so the same cable becomes a ~12 ft unfused run
through the cabin. A chafe-through anywhere along it has the full battery behind it and
nothing to open the circuit.

Fit a high-amp fuse (ANL, MEGA or Class T, 250-400 A) **within ~18 in of the trunk battery
positive**, ahead of everything. It is the only thing protecting the cabin run. Everything
downstream - starter, `PDB1`, the fuse block, PMU-16 - sits behind it. A battery master
cutoff belongs in the same place.

**2. The alternator is fused in OEM; our plan currently is not.** The factory runs
alternator B through a **100 A FL ALT** back to the link box - it does **not** join at the
starter post. Section 6.1 has the 160 A alternator joining at the starter B+ post with no
protection, which leaves an alternator-cable short unprotected all the way to the battery.
Fuse the alternator lead at **150-175 A** (160 A alternator, so OEM's 100 A does not scale
directly) close to where it joins.

**3. `w_strl` is not heavy DC.** Page 48 shows the starter relay driving starter terminal
**1 / A** - the solenoid trigger, a thin wire. Terminal **B** is the heavy lead, and it
comes from the battery, not from a relay. So `w_strl` may *route* with the heavy DC bundle,
but it takes no stud on `PDB1` and gets no heavy-gauge wire. Size it per 6.6 for solenoid
pull-in current.

Net effect on 6.19: **starter current does not pass through `PDB1`.** The starter is fed
direct from the main cable, OEM-style. `PDB1` feeds the fuse block, PMU-16 and accessories
only - so the **250 A Blue Sea 2127 with cover 2719** is the right part, not the 600 A one.

### 6.21 Loom C and the heavy DC - related but not the same bundle

Loom C now carries the radiator and condenser fan power, all EPS wiring, and the OEM
engine-room injection. It runs alongside the heavy DC, but the two are not interchangeable:

| | Heavy DC | Loom C power |
|---|---|---|
| Gauge | 2 AWG | 8 AWG and smaller |
| Switched? | No - always live | Yes, through relays |
| Protection | Main fuse at the battery only | Individually fused |
| Terminations | RADLOK, studs, lugs | Connectors per 6.7 |

They may share a routing path. They must not share a sleeve, a lug or a stud.

**The EMI problem to design around.** The two ECU-sourced EPS wires - the `Ign 6 / B12`
relay trigger and the `Aux 7 / A27` speed pulse - now run from the ECU into loom C, beside
fan motor power and a 60-80 A EPS feed. The speed pulse is a 0-5 V square wave at roughly
4 pulses/rev; fan brush noise and the EPS current step are exactly what corrupts that kind
of signal.

- Run the speed pulse as a **twisted pair with its own return**, or shielded per 6.12.
- Keep both signal wires **out of the heavy bundle** for the last stretch into the pump.
- Do not splice their grounds into the fan or EPS power grounds.


### 6.22 How the factory connects to the battery - EWD page 46, read 2026-09-17

Supersedes the partial picture in 6.20, which was read off page 48 and only showed three
of the four fusible links.

```
BATTERY + ──┬── FL MAIN 2.0L ──► F11 FUSIBLE LINK BOX ──┬─ 60A  FL ABS  ──► ABS relay
            │   (fusible link,                          ├─ 30A  FL AM2  ──► Ignition sw AM2
            │    at the battery)                        ├─ 40A  FL AM1  ──► Ignition sw AM1
            │                                           └─ 100A FL ALT  ──► Alternator B
            │
            └── heavy black, DIRECT, unfused ─────────────► STARTER terminal B
```

**Answer to the question: fusible link.** Everything except the starter leaves the battery
through **one** protected main feed and is then split by a distribution box. Only the
starter lead is a direct unfused connection.

Note: the "2.0L" in `FL MAIN 2.0L` is the **fusible-link wire size, 2.0 mm²** - not the
engine. Do not read it as a displacement when sizing a replacement.

Page 46 also shows the factory fan feeds - `30A FL RDI FAN` and `30A FL CDS FAN` off the
ENGINE MAIN RELAY - which is what loom C replaces.

**Year coverage.** The snips in `docs/electrical/ewd-snips/` are the **1990** book, which
is what could actually be verified. No 1991-1993 EWD or factory supplement was findable
online in a form worth citing. The architecture is very unlikely to have changed across
1990-93, but that is an assumption, not a verified fact. If the 1991-93 book is to hand,
snip the equivalents of pages 46, 48 and 52 and they can be diffed against these.

### 6.23 Our battery connection - mirrors OEM, settled by Daniel 2026-09-17

Same topology as the factory, with the protection scaled for a trunk battery and a long
cabin run.

```
TRUNK BATTERY +
   │
   ├── BATTERY KILL SWITCH ── at the main post
   │
   └── MAIN FUSE ── ANL / MEGA / Class T, within ~18 in of the post
         │
         ├── 2 AWG ──► RADLOK ──► STARTER B+
         │     (OEM runs this unfused, but its cable is 2 ft in the engine bay.
         │      Ours is a ~12 ft run through the cabin, so it sits behind the
         │      main fuse. This is the one place we deliberately depart from OEM.)
         │
         └── main feed ──► PDB1, glove box        [mirrors FL MAIN -> F11 link box]
               ├── fuse block
               ├── ANL 150A ──► PMU-16
               └── jump lug
```

Alternator B+ gets its own **175 A** fuse - the factory protects it at 100 A FL ALT for the
stock unit, scaled here for the 160 A alternator. It is **never** joined unprotected at the
starter post.

Standing rule, set by Daniel: **every large-gauge conductor is fused near the battery, and
one battery kill switch sits at the main post.**

Mapping, factory to ours:

| Factory | Ours |
|---|---|
| `FL MAIN 2.0L` at the battery | Main ANL/MEGA/Class T + kill switch, trunk |
| `F11` fusible link box | `PDB1` (Blue Sea 2127), glove box |
| `100A FL ALT` | ANL 175 A on the alternator lead |
| `40A FL AM1` / `30A FL AM2` | Cabin fuse block feeds off `PDB1` |
| `60A FL ABS` | Deleted - no ABS in this build |
| `30A FL RDI FAN` / `30A FL CDS FAN` off engine main relay | Loom C fan feeds, relay + fuse per 6.2 |
| Battery to starter, direct unfused | 2 AWG behind the main fuse |


### 6.24 Wire and cable are GENERIC in every BOM - set by Daniel 2026-09-17

**Wire and cable never carry a manufacturer part number in this project's BOMs.** Daniel
holds large stock of many types; any 22 AWG white Tefzel shielded cable is interchangeable
with any other. Chasing a specific part number wastes time and produces a buy list that
looks short when the shelf is full.

Instead, every wire and cable line is described so it can be matched off the shelf:

| Field | Example |
|---|---|
| Gauge | 22 AWG |
| Insulation / jacket | Tefzel (crosslinked ETFE) |
| Colour | White |
| Construction | Single conductor, shielded, tinned copper braid |
| Where it is used | EPS speed pulse, Aux 7 to pump connector B |

That is the whole spec. Manufacturer and part number columns stay blank or read `generic`.

This applies **only to wire and cable**. Connectors, contacts, seals, backshells, relays,
fuses and distribution hardware still carry real part numbers - those are not
interchangeable and getting one wrong costs a rebuild.

### 6.25 EPS speed pulse cable

Single conductor, **22 AWG**, white Tefzel, shielded. Shield grounded at the **ECU end
only**, floating at the pump, modelled per 6.12. Daniel has this in stock.

**The shield is a screen, not a return.** Single-conductor shielded has no second
conductor, so the pump's signal return goes through its own ground. Tying the shield at
both ends, or using it as the return, defeats the screening and puts pump ground current
on the drain wire.

22 AWG suits the job: the signal carries almost no current, so gauge is set by handling and
by the connector contact range. The Superseal contacts already on hand (`3-1447221-4`,
0.5 mm2) cover it.

### 6.26 Where the purchase records live

For confirming what is already owned, in order of usefulness:

| Source | Holds |
|---|---|
| Google Drive `/cars/Celica/parts invoices` | Invoices from TE, Crimp Zone, Ballenger and others - most of the car |
| Gmail, saved-receipts and receipts labels | Anything not filed in Drive |
| `TE_BOM_with_screenshots.xlsx` | Connectors, contacts, heat shrink, fittings. **No wire or cable lines** |

Note: the TE invoice PDFs in Drive are image-only scans - text extraction returns nothing
from them. They have to be read as images.

Per 6.24, none of this applies to wire and cable. Do not go looking for a wire part number
in an invoice; describe the wire and move on.


### 6.27 Shields - the rules, set by Daniel 2026-09-19. Supersedes 6.12

Five rules. They are absolute; there are no per-device exceptions.

1. **A shield is never connected at the device end.** It floats there. Always.
2. **It terminates at the ECU end only.** That is its single ground reference.
3. **None of the connectors in this build have a shell for a shield.** Do not model
   one, do not spec a connector that needs one, do not wire a drain to a connector body.
4. **A shield is cable only until it terminates at the ECU** - it is a core inside the
   cable, not a wire in its own right, right up to the ECU end.
5. **Shields pass THROUGH the bulkhead on their own pin, not on the bulkhead shell.**

Also settled: the ABS wheel-speed sensors have **two wires**. No third conductor, no
shield connection at the sensor.

**Applied 2026-09-19.** `rebuild_looms.py` strips every connector shell and deletes every
drain that landed on a device:

| Removed | Was |
|---|---|
| 7 connector shells | `crank`, `knock1`, `cam`, `wss_fl`, `wss_fr`, `wss_rl`, `wss_rr` |
| 7 device-end drains | `w_drain_crank`, `w_drain_cam`, `w_drain_knock1`, `w_drain_wss_fl`, `w_drain_wss_fr`, `w_drain_wss_rl`, `w_drain_wss_rr` |

The ECU-side runs stay: `w_drain_bh_e`, `w_drain_bh_c`, `w_drain_rear`, `w_drain_ecu_a`,
`w_drain_ecu_b`. That is the shield's real path - device (floating) through a bulkhead pin
to the ECU shield ground.

**Still to do, and it needs bulkhead pins counted first.** Rule 4 means each shielded run
becomes a **cable** - the signal conductor or conductors plus a shield core whose `source`
is the ECU-side shield termination and which has **no `target`**, so it floats at the
device. There are no cables in any file yet, so this is an all-new pass. Rule 5 plus the
6.3 "every shield gets its own bulkhead pin" rule means **7 shielded runs need 7 bulkhead
pins** where today they share one after a splice. Count the headroom before drawing:
bulkhead A is 47 cavities, bulkhead B is 21, and 6.17 just handed back B `c13` and `c14`.

### 6.28 Superseded diagrams are archived, not deleted - Daniel 2026-09-19

An old diagram goes to `archive/superseded-diagrams/`. It is never deleted - the repo
already had an `archive/` folder and that is where retired material lives.

| Archived 2026-09-19 | Replaced by |
|---|---|
| `docs/electrical/CLUSTER-LED-DIAGRAM.html` | `ST185-ClusterLED` in harness.design (`wkRX`) |
| `docs/harness/RESIDUAL-LED-FACE.md` | same - it was only a pointer to the HTML |

Per `CLAUDE.md`, nothing in `archive/` is authoritative and it is excluded from normal
agent context. It is there for "why did we do it that way", nothing else.


### 6.29 Wheel-speed shield topology - set by Daniel 2026-09-20

The VR conditioners have no shield in/out terminal, so a wheel-speed shield cannot run
unbroken from sensor to ECU. It is **two shielded segments**, each sinking at exactly one
end and floating at the other:

```
  ABS sensor           VR conditioner PCB              ECU
  (FLOAT) ═════════════ (SINK: power ground)
                        (FLOAT) ═════════════════════ (SINK: shield ground)
           segment 1                  segment 2
```

- **Segment 1** - sensor to conditioner. Shield floats at the sensor, sinks to the
  conditioner's **PCB power ground**.
- **Segment 2** - conditioner output to ECU. Shield floats at the conditioner, sinks to
  **ECU shield ground**.

Front pair (FL, FR) goes to one conditioner, rear pair (RL, RR) to the other. Two sensors
per conditioner, two conditioners.

This is consistent with 6.27: every shield still terminates at exactly one end, and never
at the device.

**Consequence for the bulkhead count.** The four wheel-speed shields die at their
conditioner - they never reach a bulkhead. Only the engine sensors need a bulkhead pin of
their own:

| Shield | Needs a bulkhead pin? |
|---|---|
| crank, cam, knock1 | **Yes** - 3 pins, engine side to ECU |
| wss_fl, wss_fr, wss_rl, wss_rr | No - segment 1 ends at the conditioner |

So **3 pins, not 7**. Measured headroom is 16 free pairs on bulkhead A and 11 on B, so
this is comfortable.

**Assumption flagged, not guessed at.** Daniel said the wheel-speed loom gets no bulkhead
connector and is a harness of its own. Taken at face value, that means it crosses the
firewall on its own grommet, not through bulkhead A - so the six `dm_bh_a_*` dummies the
split left in `ST185-WheelSpeed.harness` are leftovers from the old routing and come out.
If the front sensors are in fact meant to keep using bulkhead A, say so and they go back,
costing 2 signal pins plus 1 shield pin on A.


### 6.30 VR conditioner gets a shielded enclosure - CORRECTS 6.29

**6.29 was wrong on one point and this replaces it.** The shield does **not** sink to the
conditioner's PCB ground. Daniel is building the conditioner a **small shielded enclosure**
so the ABS shield stays **virtually one continuous shield from sensor to ECU**, isolated
from noisy supply ground.

```
  ABS sensor        VR conditioner enclosure shell        ECU
  (FLOAT) ══════════ shell ── shell ══════════════════════ (SINK: shield gnd)
                  one continuous shield, PCB isolated from the shell
```

Conditioner enclosure, per channel pair:

| Connector | Ways | Carries |
|---|---|---|
| Input LEFT | 3-pin | shielded sensor in |
| Input RIGHT | 3-pin | shielded sensor in |
| Output | combined | conditioner power in, plus shielded left and right output signals |

**The PCB is isolated from the enclosure shell.** That is the whole point - the shell
carries the shield straight through, the PCB ground never touches it, and the only
termination is at the ECU shield ground. 6.27 still holds: one shield, one termination,
never at the device.

The four ABS shields therefore reach the ECU after all, so they are back in the bulkhead
pin count - see 6.32.

### 6.31 ABS routing - set by Daniel 2026-09-20

| Pair | Runs with |
|---|---|
| **Front** (FL, FR) | Through the fenders, **with loom C** |
| **Rear** (RL, RR) | With the **fuel pump and level sender** |

Neither pair gets its own firewall crossing - they ride looms that already cross.

### 6.32 Shield bulkhead pins - the allocation rule

**First choice: every shield gets its own bulkhead passthrough pin.** Allocate them that
way whenever the pins exist.

**When they do not:**

1. **Critical sensors keep their own dedicated shield pin.** Crank and cam first - they are
   the trigger inputs, and a corrupted trigger is a dead or damaged engine. Knock next.
2. **Everything else shares.** Non-critical shields combine onto a shared passthrough pin
   to get into the cabin, then **split back out** to each device cable on the far side.
3. **They all terminate together at the ECU shield grounds** regardless of how they
   crossed.

Sharing a passthrough is a packaging compromise, not a change to 6.27 - each shield still
has exactly one termination, at the ECU.

Current headroom says it does not come to that: 16 free pairs on bulkhead A, 11 on B, and
the shield count is well under that.

### 6.33 Diagram layout standard - applies to EVERY harness diagram

Same geometry on all of them, no exceptions, so any drawing can be read without relearning it.

```
   REAR of car                              FIREWALL      ENGINE BAY + FRONT
   (leftmost)                                             (far right)
  ┌──────────────────────────────────────────────────────────────────────┐
  │  rear driver-side items         ┌──────┬──────┐                      │ DRIVER
  │                        ┌──────┐ │ BH-A │ BH-A │  engine bay AND      │ SIDE
  │                        │ ECU  │ │cabin │ eng  │  front-of-car        │ (top)
  │  ──────────────────────│ A  B │─┤      ►◄     ├──────────────────────│
  │                        └──────┘ │ BH-B │ BH-B │  driver top,         │ PASS
  │  rear passenger-side items      │cabin │ eng  │  passenger bottom    │ SIDE
  │                                 └──────┴──────┘                      │ (bottom)
  └──────────────────────────────────────────────────────────────────────┘
         left of centre ─┘          cabin pair │ engine pair
```

- **ECU A and B always adjacent**, placed **left of centre**.
- **Rear-of-car items** occupy the **leftmost** portion.
- **Driver side** in the **top half**, **passenger side** in the **bottom half**.
- **The two CABIN bulkhead halves, A and B, always sit next to each other** as a pair, to
  the right of the ECU.
- **The two ENGINE-BAY halves, A and B, sit next to each other** as their own pair,
  immediately right of the cabin pair, **faces facing the cabin pair**.
- **Engine bay devices AND front-of-car devices go in the far-right region** - driver side
  top, passenger side bottom. Front-of-car counts as right, the same as engine bay.

### 6.34 Wire lengths and the path overlay deliverable

**Lengths** come from the **Toyota body repair manual dimensions**, using a best-fit path -
not guessed, not scaled off a screen.

**Every harness gets a path image** alongside its diagram:

- SVG or PNG, one per harness
- built on the **body manual images** actually used for that harness
- with a **red line overlaid** showing the cable harness path
- the source figures cited so the estimate can be rechecked

**Source, found 2026-09-20 in Google Drive** - not a blocker after all:

| File | Size | Use |
|---|---|---|
| `93 Repair - Chassis & Body.pdf` | 33 MB | Primary. Body dimensions and the figures to overlay |
| `Repair Manual 1990 BGB.pdf` | 20 MB | Cross-check |
| `Body_Repairs_General_Body_Repairs.pdf` | 2 MB | General body-repair sections |

The repo only holds the 1990 *electrical* snips, so the body pages have to be pulled from
Drive and the ones actually used committed alongside each overlay - same pattern as
`docs/electrical/ewd-snips/`. Suggested home: `docs/body/brm-snips/`.

Every length must trace to a cited figure. A length with no citation is a guess and does
not go in the build list.

---

## 6.35 VR conditioner enclosures - connectors and box sizing

Settled with Daniel 2026-09-21. The boards are tiny, so the connectors set the box size.
Two identical boxes: one front (FL/FR), one rear (RL/RR), per 6.31.

### Why M8 and not DT/DTM

6.30 wants the ABS cable shield continuous from sensor to ECU, with the PCB isolated from
the shell. There are only two ways to carry a shield across an enclosure wall:

| Method | How it works | Verdict |
|---|---|---|
| Discrete shield pin | Shield crimped into an ordinary contact, jumpered pin-to-pin inside the box | Works, but it is a pigtail at both walls. Adds inductance exactly where we are trying to keep the screen tight. AT/ATM and DT/DTM are all-plastic, so this is the only option with those families |
| Metal shell, 360 degrees | Shield clamps to the connector body, body bonds to the panel, panel carries it to the next connector body | No pigtail. This is what 6.30 actually describes when it says "shielded enclosure" |

So the conditioner boxes are the one place on this car that uses metal-shell connectors.
Everything else stays as 6.27 says - shields are cable-only, no shell, floating at the
device end.

### Parts

All three positions use the same 4-way shieldable M8 so there is one contact system to
stock and one crimp setup. Inputs are female, output is male, which makes it physically
impossible to plug a sensor lead into the output.

| Position | Part number | Manufacturer | Contacts used | Notes |
|---|---|---|---|---|
| IN-L (sensor) | 86 6618 1121 00004 | binder | VR+, VR-, 1 spare | Female, shieldable, THT, IP67, M10x0.75 front fastened |
| IN-R (sensor) | 86 6618 1121 00004 | binder | VR+, VR-, 1 spare | Same part |
| OUT (to ECU) | 86 6319 1121 00004 | binder | 5V, GND, OUT-L, OUT-R | Male, shieldable, THT, IP67, front fastened |

Verified ratings: 4.0 A per contact, 50 V AC / 60 V DC, IP67, -40 to +85 C, shield
terminated by a shielding plate against the panel. Roughly USD 16 each, so about USD 96
of connectors for both boxes before mating cable plugs.

Ratings are far beyond what these circuits need - the conditioner runs off the ECU 5 V
sensor supply and the outputs are logic-level pulses. The parts are chosen for the shield
path and the size, not the current.

### Box

Requirement, not a confirmed part number:

- Diecast aluminium, conductive. The shielding plate needs bare metal against the panel
- Internal envelope at least 50 x 50 x 30 mm
- One connector per face: IN-L left, IN-R right, OUT back. Keeps each face down to about
  30 mm of usable width and makes the cable routing fall out naturally
- Panel cutout 10.2 mm with an anti-rotation flat, roughly 10 mm edge margin
- PCB on nylon standoffs, not metal. 6.30 - the board floats, the shell carries the screen
- MASK THE THREE CONNECTOR LANDINGS BEFORE POWDER COAT. A coated panel breaks the shield
  path and the fault will look like sensor noise, not a coating problem

Hammond's small diecast range is the obvious place to look. Confirm the exact part against
the connector flange diameter and the board outline before ordering.

### Open

- Mating cable plugs and the shielded cable between sensor and box are still to spec
- -40 to +85 C is fine in the cabin. If either box ends up in the engine bay, re-check it

---

## 6.36 Bulkhead pin ordering

Settled with Daniel 2026-09-21. Two separate things that were being confused:

1. **Pin assignment stays grouped by function.** Injectors together, coils together,
   sensor supplies together. This is what makes the bundle sane to build and to fault-find,
   and it is why the A-ECU schematic shows a lot of crossing lines - ECU pin order and
   bulkhead pin order do not match, and they should not have to.
2. **Wiring-table row order is free.** Rows do not have to run 1, 2, 3 or A1, A2, A3. They
   are ordered for whatever reads cleanest on the drawing.

The one hard rule: **the mating connector follows the exact same order.** A pin table and
its mate are always read together, so if one is reordered the other is reordered with it.

Schematic crossings are not a defect to chase. Nothing is built from the picture - the
build follows the pin table.

---

## 6.37 CSB3 enclosure - single AMPSEAL connector

Settled with Daniel 2026-09-21. One connector carries every CSB3 terminal. The
board is 33 x 33 x 5 mm, so the connector sets the box size, same as 6.35.

### Pin count comes from the ECUMaster manual, not from what we use today

From `switchboardManual.pdf` v2.1, section 3:

| Group | Terminals | Count |
|---|---|---|
| Low side outputs | L1-L4, 0.5 A each | 4 |
| Analog inputs | A1-A8, 0-5 V, 10-bit, software pull-up | 8 |
| Switch inputs | S1-S8, switched to ground | 8 |
| CAN | CAN H, CAN L | 2 |
| Power | +12V (switched), GND | 2 |
| Sensor supply | +5V, SGND | 2 |
| | **Total** | **26** |

This build currently lands 14 of those. The other 12 are brought out anyway so a
spare channel never means opening the box.

Board spec worth recording: AEC-Q Grade 1, -40 to +125 C, 6-22 V, CAN 2.0 A/B up
to 1000 kbps, on-board 120 ohm terminator behind a jumper. **That jumper stays
OPEN** - 6.x already puts the two bus terminations at the ECU and the Pi.

### Why AMPSEAL and not AMPSEAL 16

AMPSEAL 16 tops out at 12 positions. It is the nicer, smaller system and it is
simply not big enough. Classic AMPSEAL goes 8 / 14 / 23 / 35, so 35 is the only
size that takes all 26 in one connector.

AMPSEAL headers are ECU connectors by design - flanged, sealed, made to mount
through an enclosure wall. That is exactly this job.

### Parts

| Role | Part number | Notes |
|---|---|---|
| Enclosure side | **1-776231-1** | 35-pos vertical PCB header, WITH flange seal, black, gold |
| Mating plug | **776164-1** | 35-pos plug housing, black |
| Socket contacts | **770854-3** | Gold, loose piece. 26 needed plus spares |
| Cavity seal plugs | **770678-1** | 9 needed for the unused cavities |
| Wire relief | **776463-1** | Two halves per housing, so order 2 |
| Hand crimp tool | **58440-1** | |

Gold, not tin, for two reasons: the analog inputs read millivolts, and gold is
rated -40 to +125 C against tin's +105 C. Rated up to 17 A per contact, 1.3 mm
pin and socket, IP67, glass-reinforced PBT.

**Wire gauge is a hard constraint: 20-16 AWG, insulation 1.7-2.7 mm.** 22 AWG
will not crimp reliably in these contacts. Signal runs to this box are 20 AWG
minimum - do not default to 22 out of habit.

### Cavity assignment

Grouped by function per 6.36, and deliberately ordered so the four switching
outputs sit as far as possible from the analog inputs and the CAN pair.

| Cavity | Signal | | Cavity | Signal |
|---|---|---|---|---|
| 1 | +12V (ignition switched) | | 15 | S1 |
| 2 | GND | | 16 | S2 |
| 3 | +5V sensor supply out | | 17 | S3 |
| 4 | SGND sensor ground | | 18 | S4 |
| 5 | CAN H | | 19 | S5 |
| 6 | CAN L | | 20 | S6 |
| 7 | A1 | | 21 | S7 |
| 8 | A2 | | 22 | S8 |
| 9 | A3 | | 23 | L1 low side |
| 10 | A4 | | 24 | L2 low side |
| 11 | A5 | | 25 | L3 low side |
| 12 | A6 | | 26 | L4 low side |
| 13 | A7 | | 27-35 | spare, seal plug 770678-1 |
| 14 | A8 | | | |

CAN H and CAN L on 5 and 6 so the twisted pair stays twisted right up to the
connector.

### Build

Wires solder to the CSB3 pads - the board has no connector of its own. So:
header flange-mounts in the box wall, 26 short wires run from its solder tails
to the board pads, contacts are crimped on the harness side only.

- Box: diecast aluminium. The 35-position right-angle header is 76.9 x 59.4 mm
  overall; confirm the vertical version's flange footprint off the TE drawing
  before buying a box, then allow about 15 mm around it
- Working estimate, to be confirmed: roughly 90 x 70 x 35 mm internal
- Strain relief on the harness side is the 776463-1 pair, not a zip tie
- Leave enough service loop inside to lift the board out without desoldering

### Open

- Confirm the vertical header flange footprint and hole pattern from the TE
  customer drawing, then pick the box part number
- If the box comes out too big, the lever is the four low-side outputs. Dropping
  L1-L4 takes it to 22 terminals, which fits a 23-position AMPSEAL (plug
  770680-1, vertical sealed header 1-776228-1) with one spare. Only worth doing
  if illuminated switches are off the table for good

---

## 6.38 Dash and CAN device power - PMU outputs

> **SUPERSEDED 2026-09-22 by 6.48 - there is no PMU.** The cluster and Pi come off
> a relay, the CSB3 off a permanent fused feed. Everything below about *why* these
> devices need their own clean feed, the DTM4 house standard, the load figures and
> the clean-shutdown requirement still stands. Only "PMU output" is wrong.

Settled with Daniel 2026-09-21. The cluster, the CSB3 and the RealDash Pi all
come off PMU-16 outputs, not the CAN cable and not the fuse block.

### Why not the CAN cable

The obvious-looking answer was the Link CAN cable, which does carry 12V. It does
not come from the ECU. Per Link's own spec for CANLTW, only CAN H and CAN L land
on the ECU's 6-pin connector; the 12V and GND are **500 mm flying leads** the
installer feeds from their own source. The DTM4 at the device end is:

| DTM4 pin | Function |
|---|---|
| 1 | 12V - flying lead, your own fused feed |
| 2 | Ground - flying lead |
| 3 | CAN L - from the ECU |
| 4 | CAN H - from the ECU |

The XtremeX has no 12V output at all - the quick start guide lists +5V Out and
+8V Out only. So there was never a supply to borrow.

**Adopt that DTM4 pinout as the house standard for CAN device drops** so
anything Link-compatible plugs straight in. Just feed pin 1 properly.

### Loads

| Device | Draw | At 12 V |
|---|---|---|
| Pi 5 + official 7" Touch Display 2 | 5 V @ 5 A = 25 W (Raspberry Pi's own PSU spec) | ~2.5 A via a DC-DC, ~3.1 A at a 9 V cranking dip |
| ESP32 cluster + display | order of 10 W | under 1 A |
| CSB3 | 6-22 V direct, board draw negligible; L1-L4 add up to 0.5 A each if loaded | under 2 A worst case |

The Pi is the whole reason this is not a fuse-block job. It wants 25 W of clean
5 V in a system that dips to 9 V cranking and spikes on load dump.

### Feed

- One PMU 15 A output per device, three outputs. Current limit set per device,
  not one shared feed
- Pi output limit around 8 A - well above the ~2.5 A steady draw, so converter
  inrush does not trip it, and well under what the wire takes. 16 AWG is ample
- Pi needs a **12 V to 5.1 V DC-DC rated 5 A continuous minimum**, tolerant of
  6-16 V in. Not a cheap buck module - it has to ride out cranking
- CSB3 takes 12 V directly, no converter. It is specified 6-22 V

### The real reason for the PMU: clean shutdown

A Pi is a Linux box. Cutting power at key-off corrupts SD cards, and it will do
it slowly enough that it looks like bad luck rather than a design fault.

1. PMU holds the Pi's output live for a set delay after ignition drops
2. The Pi sees ignition go false - it is already on the CAN bus for RealDash, so
   it can read that state rather than needing another wire
3. A shutdown script runs
4. The PMU output drops after the delay expires

Set the delay from a measured shutdown, not a guess - time it on the bench and
add margin. 45-60 s is the starting point.

### Open

- Pick the DC-DC converter. Needs 5 V 5 A continuous, wide input, automotive
  transient rating
- Confirm the PMU can hold an output after ignition drops on a timer in its
  own config, rather than needing the ECU to command it
- Measure the Pi's actual shutdown time before fixing the hold delay

---

## 6.39 Sealed devices - where the harness stops

Settled with Daniel 2026-09-21. **The harness ends at the device connector.**

The TrackCluster and the RealDash Pi are each a single sealed device with their
own buck converter and CAN transceiver inside. Neither gets a drawing. Neither
appears in a BOM beyond its mating connector.

What that means in practice:

- The harness delivers four wires to each: 12V, GND, CAN H, CAN L. Nothing else
  crosses that boundary
- **No DC-DC converter in the harness.** 6.38 originally spec'd a 12V-to-5.1V
  5 A supply for the Pi. That is inside the sealed device. Struck
- No 5 V anywhere near these two. The harness is 12 V only at that connector
- Their internals - display, transceiver, regulator, SD card - are out of scope.
  If one dies it is swapped as a unit

The current draw still matters even though the converter is theirs: the Pi 5
with the official 7" Touch Display 2 pulls 5 V at 5 A internally, so budget
about 2.5 A at 12 V steady and more at switch-on. That sizes the PMU output, the
fuse and the wire - not a converter we buy.

This supersedes the DC-DC line in 6.38 and the "confirm the Pi model" open item.

---

## 6.40 CSB3 enclosure connector - REVISED, Deutsch HD30 not AMPSEAL

Supersedes the parts table in 6.37. The pin count, cavity assignment and build
notes in 6.37 all still stand - only the connector family changes.

Daniel lifted the "AMP style" constraint and asked for the best part. It is not
AMPSEAL.

### Why the change

AMPSEAL 35 works but it is a big rectangular connector on a 33 mm board: the
35-position header is 76.9 x 59.4 mm, about 4,570 mm2 of panel face. Shell size
24 of the Deutsch HD30 range holds **33 contacts, all size 20**, in a 50.8 mm
circular flange - roughly 2,030 mm2, under half the area. On a box whose size is
set entirely by its connector, that halves the box.

Three more things fall out of it, and together they matter more than the size:

| | AMPSEAL 35 | HD34-24-33 |
|---|---|---|
| Panel face | 76.9 x 59.4 mm rectangular | 50.8 mm round |
| Contacts | 770854-3, a system used nowhere else on this car | **The same size 20 contacts as bulkhead A** |
| Crimp tool | 58440-1, another tool | The HDP20 tool already needed |
| Sealing | IP67, -40 to +125 C | IP68, -55 to +125 C |
| Spare ways | 9 | 7 |
| Panel cutout | rectangular, hard to cut cleanly | round hole, trivial on a mill or a hole saw |

Bulkhead A is HDP24-24-47, which is 5 size 16 plus 42 size 20 - the same shell
size 24 and the same contact system. So the CSB3 box lands on one contact
family, one crimp tool, one removal tool for the whole car.

### Parts

| Role | Part number | Notes |
|---|---|---|
| Enclosure side | **HD34-24-33PE** | HD30 flange-mount receptacle, shell 24, 33 size-20 PINS, E seal. Pins, because the box is dead when the plug is off |
| Mating plug | **HD36-24-33SE** | HD30 plug, 33 SOCKETS, E seal. Sockets on the harness so the live 12 V side is shrouded when unplugged |
| Contacts, harness side | **0462-201-2031** | Size 20 solid socket, 20 AWG. Already on the buy list for bulkhead A |
| Contacts, box side | **0460-202-2031** | Size 20 solid pin. Same |
| Cavity plugs | **0413-204-2005** | Size 20 sealing plug, red. 7 needed |

E seal to match bulkhead A, so one seal type across the car.

### Box

- Panel face at least 51 mm across the flange, so about **70 x 70 mm** face with
  margin. Mounting holes on a 43.08 mm circle, cutout per the TE drawing
- Working envelope, to be confirmed: roughly **70 x 70 x 40 mm** internal
- Same build as 6.37: flange-mount the receptacle, run 26 short wires from its
  contacts to the CSB3 solder pads, nylon standoffs under the board

### Still to confirm before ordering

- **That HD30 and HDP20 genuinely share the size 20 contact.** They sit in the
  same TE technical manual and the arrangements line up, which is why this is
  the recommendation - but the datasheet page did not state it outright, and the
  whole benefit rests on it. Check the TE customer drawing for HD34-24-33PE
- The HD36 plug part number and its clamp/backshell options
- Behind-panel depth of the receptacle, which sets the box depth

### Unchanged from 6.37

26 terminals, the cavity assignment grouped by function, wire 20-16 AWG, and the
CSB3 on-board 120 ohm terminator jumper stays OPEN.

---

## 6.41 Loom boundaries - what belongs in A, B and C

Settled with Daniel 2026-09-22. This section is binding on every harness rebuild.
It exists because pass 2 found ECU-A wires riding bulkhead B, EPS wires riding
bulkhead B, and the CSB3 split across three drawings.

### The looms are independent

```
ECU-A  ->  bulkhead A cabin  ==  bulkhead A engine  ->  engine bay
ECU-B  ->  bulkhead B cabin  ==  bulkhead B engine  ->  engine bay
```

Loom A does not dictate loom B and loom B does not dictate loom A. They are two
separate looms that happen to leave the same ECU.

### Which loom a wire belongs to

1. **The ECU pin decides.** A pin on ECU-A puts the wire in loom A. A pin on
   ECU-B puts it in loom B.
2. **Anything not bound for its own bulkhead branches at the ECU connector** and
   runs direct to its loom. It does not travel down loom A or B to a bulkhead
   first.
3. **Looms A and B carry only wires entering the engine bay through their own
   bulkhead.** Nothing crosses from loom A or B into another loom on the
   engine-bay side.
4. **Cabin-side branching is allowed.** Rule 3 is about the engine-bay side. A
   wire may enter on loom A or B and branch under the dash to a cabin device.
   Stated example: the reverse switch comes in on A or B and branches under the
   dash to the CSB3.

### EPS

EPS lives in loom C. Only loom C. The pump power, the pump ground, the relay,
the enable feed and the ECU trigger (Ign 6 / ECU-B B12, per 6.16) are all loom C.
None of it belongs on bulkhead B.

### Cabin accessory loom - new drawing

The CSB3, the cluster LED loom and the dash devices get their own drawing rather
than being split across A-ECU, B-ECU and CAN. The CSB3 HD36-24-33SE connector
(6.37 map, 6.40 family) is owned there, once, and every other drawing that
touches it shows a cross-reference node with no part assigned.

### Wheel speed - split front and rear

Settled 2026-09-22. The two VR conditioner boxes do not share a loom.

| | Front | Rear |
|---|---|---|
| Sensor drops | FL, FR | RL, RR |
| VRC box | front box, **loom C** | rear box, **rear trunk loom** |
| Also on that loom | the rest of the engine room | fuel level sender, fuel pump |

The conditioner **outputs** merge into whichever loom holds their assigned ECU
pin, per the rule above: FL -> ECU-A A23 -> loom A. FR, RL, RR -> ECU-B B21, B20,
B19 -> loom B. Fuel level -> ECU-B B24 -> loom B.

**Front raw VR pairs - no firewall crossing (Daniel, 2026-09-25).** The front
sensor drops run in a **fender sub-loom of loom C** (the engine room harness),
drawn separately in `ST185-WheelSpeed.harness`. Loom C leaves through the driver
fender, not a bulkhead, so these pairs get no bulkhead cavity and no drawing
should show one. Not an open item.

Putting the rear box in the trunk rather than the cabin is the right way round for
noise: the raw VR millivolts travel a few feet from the rear hubs to the box, and
the conditioned square wave makes the long run forward.

### Rear trunk loom - new drawing

Third new loom, alongside loom C and the cabin accessory loom. Carries:

- RL and RR sensor drops, screened, into the rear VRC box
- The rear VRC box: 5 V and ground in, two conditioned outputs forward
- Fuel level sender - uses the **OEM connector**, both halves on hand. Settled;
  no part to source.
- Fuel pump power and ground - its own circuit, see below

Fuel level and fuel pump come **out of** `ST185-B-ECU`, where they sit today.

#### Physical layout

Settled 2026-09-22.

- The **rear VRC box** sits at the rear driver-side frame, in the back seat area.
- The **fuel tank** is all the way back in the trunk.

So the pump and level-sender runs are long, and the VRC is not near either. The
pump and sender wires **run in the same bundle as the VRC harness for packaging**,
but their connectors are in different places. Nothing is co-located just because
it shares a loom.

#### Junction: an inline connector, signals only

The signal side of the trunk loom meets the cabin looms at one **inline
connector**, not a bulkhead. Forward of it the conductors split by ECU pin into
loom A or loom B as the rule above requires.

Seven conductors cross it:

| Conductor | Forward to |
|---|---|
| RL pulse out | ECU-B B20, loom B |
| RR pulse out | ECU-B B19, loom B |
| VRC +5 V in | ECU +5 V rail |
| VRC ground in | Gnd Out rail |
| Rear output cable screen | ECU-end shield termination (see 6.42) |
| Fuel level SIG | ECU-B B24, loom B |
| Fuel level GND | Gnd Out rail |

**Part, all on hand:** `DT04-12PA` receptacle + `DT06-12SA` plug with `W12P` /
`W12S` wedgelocks - a sealed 12-way Deutsch DT pair, two sets owned and previously
unassigned. Twelve ways covers seven with five spare, on the size 16 contacts
already in stock.

#### Fuel pump - its own circuit, its own connector

The pump is a **Walbro F90000295**, 450 LPH (`FUEL-SYSTEM.md`). It does not share
the inline connector with anything.

| | |
|---|---|
| Running current | **14.4 A at 13.5 V**, Radium bench test |
| Design current | **20 A** - E85 draws more than gasoline, and a 14.4 V charging system pushes it up again |
| Inrush | a brushed DC motor pulls several times running current for tens of milliseconds at switch-on. Industry hardwire kits for this pump ship a **30 A fuse and a 40 A relay**, which is the practical answer to it |
| Fuse | 25-30 A |
| Wire | **12 AWG** feed and ground. At 20 A over a trunk-length run, 12 AWG holds the drop near 0.4 V; this pump's flow is voltage-sensitive, so do not go smaller to save room |
| Relay | dedicated, per the high-consumer rule in 6.43 |
| Ground | local chassis stud in the trunk, not run forward |

**Connector: the pump's own.** It comes with one, 12 inches from the pump, and
that is the only break the circuit needs. Running 12 AWG unbroken from the relay
to that connector is better than adding a second joint in a 20 A circuit.

If a service disconnect is wanted anyway, the contact to use is Deutsch **size 12**
(`0460-220-1231` pin / `0462-210-1231` socket, 20 of each on hand, rated 25 A) -
not the size 16 used elsewhere, which tops out near 13 A and would be undersized.

Correcting the earlier estimate: 60 A is the right order for the **inrush
transient**, not for steady draw. Wire and fuse are sized on continuous current;
the contact only has to survive the spike, and contact ratings are continuous
thermal ratings, so a 25 A contact is not troubled by a 60 A millisecond event.

### Known violations to fix, found 2026-09-21

| Where | Violation |
|---|---|
| Bulkhead B cavity 13 | Carries ECU-A A27 (Aux 7, MRS SPD) |
| Bulkhead B cavity 14 | Carries MRS EPS enable from the cabin fuse block |
| Bulkhead B cavity 12 | Carries the CSB3 reverse switch out to the engine bay |
| Bulkhead A cavities 11 / 28 | Carry ABS wheel speed FR |
| ECU-B B12 | Reads notConnected on A-ECU, but 6.16 makes it the EPS trigger |
| CSB3 | Owned across three drawings instead of the cabin accessory loom |

### The loom list after this section

| Loom | Drawing | Scope |
|---|---|---|
| A | `ST185-A-ECU` + `ST185-A-engine` | ECU-A pins through bulkhead A |
| B | `ST185-B-ECU` + `ST185-B-engine` | ECU-B pins through bulkhead B |
| C | `ST185-EngineRoom-C` | engine room, EPS, front VRC, front sensor drops |
| CAN | `ST185-CAN` | CAN backbone |
| Cabin accessory | new | CSB3, cluster LEDs, dash devices |
| Rear trunk | new | rear VRC, rear sensor drops, fuel level, fuel pump |

`ST185-WheelSpeed` and `ST185-ClusterLED` are absorbed by the looms above; they
stop being drawings of their own.

### Parts selection

Before speccing any connector, contact or seal, read `docs/sourcing/README.md`.
Order is: what Daniel already owns, then TE Connectivity (free samples preferred),
then anything else. The on-hand list is `docs/sourcing/te-on-hand-bom.csv`.

Two facts from that list bear on this section directly:

- **No size-20 contacts on hand**, against roughly 300 size-16. Bulkhead A and the
  6.40 CSB3 connector both need size 20.
- The on-hand `HD34-24-21SN` / `HD36-24-21PN` HD30 pair was weighed against the
  6.40 connector for the CSB3 box and **not** chosen - see below. It stays
  unassigned and available.

### CSB3 connector - 6.40 stands

Settled 2026-09-22. The CSB3 box keeps the 6.40 pair, `HD34-24-33PE` receptacle
and `HD36-24-33SE` plug, bought new with 26 size-20 sockets.

The 21-way HD30 pair already on the shelf was the cheaper road and was rejected on
merit: it would have put pins on the harness and left the live 12 V unshrouded when
unplugged, and 21 ways cannot bring out all 26 CSB3 terminals, which is the whole
point of 6.37 - a spare channel must never mean opening the box.

So size-20 contacts are a confirmed buy: 26 sockets for this box, plus bulkhead A's
own count, from TE direct. None are on hand and DigiKey showed the socket at zero
stock on 2026-09-21.

### Open

- Fuel pump running current, which decides whether the pump pair stays in the
  trunk inline connector or gets its own. See the rear trunk loom above.
- `docs/RECONCILIATION-RULES.md` still lists `ST185-Signal.harness` and
  `ST185-Power.harness` in its source-of-truth table. The `rebuild/` A/B/engine
  split replaced those. Update the table once this restructure lands, not before,
  so it is rewritten once.

---

## 6.42 Wheel speed shielding - segmented, not continuous

Settled with Daniel 2026-09-22. Supersedes any earlier assumption that a screen
runs unbroken from sensor to ECU.

**A continuous shield is not practical here and is not being built.** The screen
is segmented at the VR conditioner box. The box case joins the two segments into
one screen node, and that node is grounded at one point only: the ECU shield
splice (`SHIELD-RULES.md` §6.30 is the governing wording; corrected 2026-09-25,
the earlier text here said the output screen floats at the box, which contradicted
§6.30). This is what makes the small enclosures buildable - a continuous screen
would force a shielded connector and a 360 degree termination at every break.

### The two segments

| Segment | Screen terminates | Screen floats |
|---|---|---|
| Sensor drop: wheel to VRC box | **VRC case** (IN pin 3, ring terminal on the case) | at the sensor |
| VRC output: box to ECU | **VRC case** at the OUT shielding plate **and** the ECU shield splice (front A7, rear B17) | nowhere - it is the one path to ground |
| FR output (exception, §6.30) | ECU shield splice `sp_shield_b` / B17 only | at the VRC (never touches the front case, which is on A7) |

Both VRC boxes follow this - front and rear, identically.

Consequences that must show up in the drawings:

- Each ABS sensor drop carries **its own screen**, terminated on the case of the
  box it lands in. Not spliced to a neighbour, not carried through.
- The VRC output cable screen is a conductor that runs the whole way forward and
  lands at the ECU end. On the rear loom it crosses the inline connector as one of
  the seven signal conductors.
- The box case is a screen termination point. It is still isolated from chassis
  per 6.35 - nylon hardware, board on nylon standoffs. Screen and chassis are not
  the same thing.

### Routing after the box

**The ABS sensor drops take their own paths once they leave the box** - separate
from any adjacent harness. They do not get bundled with the output cable, the
pump feed, or anything else. Raw VR output is millivolts; it gets its own route.

Forward of the box the conditioned outputs are square waves and may share a bundle,
which is why the pump feed running alongside the VRC harness is acceptable.

---

## 6.43 Power architecture - what the PDU owns and what gets a relay

Settled with Daniel 2026-09-22. "PDU" here is the **ECUMaster PMU-16** already in
`ST185-EngineRoom-C`; the cabin PDB is the stud/busbar block, a different thing.

### The split

| Class | Switched by | Examples |
|---|---|---|
| Internal low-power and accessory circuits | **PDU outputs, directly** | dash devices, CSB3, cluster, lighting, wipers, interior |
| High consumers | **their own individual relay**, coil driven by the PDU or the ECU | fuel pump, radiator fan, condenser fan, EPS pump, starter |

The PDU owns **most** of the low-power side. A high consumer never shares a relay
with another high consumer, and never sits on a PDU output alone.

### Battery kill

> **WITHDRAWN 2026-09-22.** Manual master cutoff only - see 6.48. The paragraph
> below recorded an idea that was dropped; the HCR150 is just the EPS pump relay.

Daniel wants a high-current relay acting as the battery kill, driven by the PDU
rather than only by a mechanical switch.

On hand and suited: **`1416010-1` / V23132-A2001-B200, the TE HCR150** - SPST-NO,
130 A, 12 V coil at 3.9 W, IP67, flange mount, screw terminals. Two are owned and
one is already spoken for by the EPS pump relay, which leaves exactly one.

Three things to settle before this is designed in. None are guesses; all three
will bite if skipped:

1. **Does it sit in the starter path?** 130 A carries the whole car but not
   cranking current, which runs several hundred amps. An HCR150 works as a
   disconnect for everything *except* the starter feed. If it has to break the
   starter circuit too, it is the wrong part and this needs a proper contactor.
2. **The PDU cannot be downstream of its own kill relay.** If the relay cuts power
   to the PDU, the PDU drops out, the coil de-energises, and nothing can re-close
   it. The PDU feed has to come from ahead of the relay, or the relay has to be
   latching.
3. **Killing the battery does not stop the alternator.** A running engine keeps
   generating, and opening the main feed on a live alternator is how load dump
   kills electronics. A kill circuit needs to drop the alternator excitation as
   well, or the engine first.

A NO relay is the right fail-safe shape for this - lose the coil, lose the power.
That is also why the coil draw matters: 3.9 W, about 325 mA, held continuously
whenever the car is live.

### Correction worth recording

The TE BOM in `docs/sourcing/` lists **no solid-state relays**. The four relay
types on it are all electromechanical:

| Part | What it is |
|---|---|
| V23074-A*, `5-1393292-8` / `4-1904124-2` / `6-1419137-4` | micro ISO, 30 A |
| V23132-A2001-B200, `1416010-1` | HCR150, 130 A |
| V23134-J1052-X281, `1-1393304-0` | F7 series PCB power relay |
| V23134-J0052-X429, `1-1414147-0` | F7 series PCB power relay |

Daniel confirmed 2026-09-22 that he owns no solid-state relays - the earlier
mention was a slip. The battery kill is the electromechanical HCR150 above.

### Closed

All four open items here were settled 2026-09-22:

- **How much the PDU owns** - option B, defined by junction-block injection points
  rather than by circuit. See **6.44**.
- **Kill relay in the starter path** - no. See **6.45**.
- **PDU feed relative to the kill relay** - disregarded at Daniel's direction.
- **Alternator excitation** - dropped by PDU sequencing before the relay opens.
  See **6.45**.

---

## 6.44 How the PDU is actually used - feed buses, not circuits

> **SUPERSEDED 2026-09-22 by 6.48 - there is no PDU.** AM1 and AM2 revert to plain
> fused feeds from the PDB. The reasoning below is kept because it is still the
> reason both junction blocks stay: **the injection-point constraint is what makes
> option B work at all**, PDU or no PDU.

Settled with Daniel 2026-09-22. Resolves the 6.43 / redistribution-doc conflict in
favour of **option B**, with the granularity defined properly.

### The constraint that decides everything

**Inside a junction block, fuses share internal buses.** You cannot feed one
fuse's input without cutting into the block. So "move a few circuits to the PDU"
is not free-form - the only places a PDU output can land without dash surgery are
the **upstream injection points the J/B already has**.

That is the whole answer. The granularity available is the injection list, not the
fuse list.

For J/B No.1 there are exactly three:

| Injection point | Bus | Feeds |
|---|---|---|
| `1I-1` | always-hot | STOP, ECU-B, DEFOGGER, taillight relay battery side |
| `IE1-10` | AM1 | ignition switch I9-4 |
| `IE1-17` | AM2 | ignition switch I9-10 |

### What the PDU takes

| Bus | Owner | Why |
|---|---|---|
| AM1 -> `IE1-10` | **PDU** | Ignition-switched. Makes the PDU the ignition master: load-shed during crank, clean drop on kill, one place to kill the dash |
| AM2 -> `IE1-17` | **PDU** | Same |
| Always-hot -> `1I-1` | **plain fused feed from the PDB** | Must stay hot regardless, so there is no control to gain - and it carries DEFOGGER's 30 A |
| R/B No.2 POWER 30 A (windows, locks) | **OEM fuse** | High current, no control value, already beside the glove box |
| R/B No.4 HEATER 40 A (blower) | **OEM fuse** | Same |
| Everything inside J/B No.1 | **untouched** | Wiper, gauge, turn, CIG, ECU-IG, IGN, STOP, TAIL, ECU-B, DEFOGGER keep their factory fuses and factory branch wiring |

**Nothing in the dash is rewired.** Two wires from the glove box to two existing
cavities is the entire change.

### Channel budget

| | Channels |
|---|---|
| HEAD LH, HEAD RH, HAZ-HORN, DOME, RTR (J/B2 injection) | 5 |
| TrackCluster, CSB3, RealDash Pi (6.38) | 3 |
| Battery-kill relay coil (6.43) | 1 |
| **AM1, AM2 (new here)** | **2** |
| Alternator excitation (see below) | 1 |
| **Used** | **12 of 16** |
| **Spare** | **4** |

Wiper park on O8 stays as written in redistribution §3.1 - optional, not counted.

### Measure before committing AM1 and AM2

40 A and 30 A are **fusible-link ratings, not loads**. A PMU output is 25 A, and
paralleling costs a second channel. Actual draw decides whether each bus is one
channel or two, and if both need two the budget goes to 14 of 16.

This is measurable on the stock car with a clamp meter before anything is
unplugged - add it to step 2 of the redistribution execution order, alongside the
2E-2/3 and 1I-1 probes already listed there.

### Why not more

Every further circuit would mean opening a junction block to reach a single fuse
input. That is the dash rewiring this decision exists to avoid, and the PDU's
value on a 15 A gauge-cluster fuse is close to zero anyway.

### Files affected

**None new.** The injection loom Daniel expected to need already exists - loom C
(`rebuild/ST185-EngineRoom-C.harness`) already carries `oem_jb1_1i`, `oem_jb1_1h`,
`oem_ie1`, `oem_rb2`, `oem_rb4` and the three J/B2 blocks. AM1 and AM2 become two
more wires from `pmu` to `oem_ie1` in that same file.

---

## 6.45 Battery kill - final shape

> # WITHDRAWN 2026-09-22 - see 6.48
>
> There is no electronic battery kill. Daniel's call: **a manual master cutoff in
> the trunk, and nothing else.** No relay, no CSB3 channel, no sequencing.
>
> Two findings below are worth keeping and are carried into 6.48:
>
> - A four-cylinder petrol starter draws 100-300 A cranking, so a 130 A HCR150
>   could never have been in the starter path. The manual cutoff is sized for the
>   whole car including the starter cable, which is the right answer anyway.
> - Opening a master switch on a running alternator is a load dump. Buy a switch
>   with an auxiliary excite-kill terminal.
>
> Everything else in this section is dead. The HCR150 is just the EPS pump relay.

Settled with Daniel 2026-09-22, closing the three questions raised in 6.43.

### 1. The kill relay is not in the starter path

A four-cylinder petrol starter draws **100-300 A cranking**, highest in the first
second, and the 3S-GTE's gear-reduction unit sits in the upper half of that.
The HCR150 is 130 A continuous. It cannot carry cranking current and is not asked
to.

So the car has **two separate things, and they must not be confused**:

| | What it is | Covers |
|---|---|---|
| **Mechanical master cutoff**, trunk, beside the main fuse | The real master switch, already on the buy list | Everything including the starter cable |
| **HCR150 under PDU control** | A main-bus disconnect for the cabin and accessory side | Everything downstream of the PDB except the starter feed |

The starter stays on the direct battery cable per 6.20. Calling the HCR150 a
"battery kill" in shorthand is fine; wiring it as if it were the FIA master switch
is not.

### 2. PDU feed relative to the kill relay

Daniel's call: disregard. Not treated as a design constraint.

### 3. Alternator excitation drops with the kill

Required. Opening a main feed on a live alternator is a load dump, and the engine
keeps running on a kill that only opens the battery.

The PDU already has the logic to do this with no extra hardware - it is a
**sequenced shutdown**, not a circuit:

1. PDU drops the alternator excitation output
2. short delay, long enough for field collapse
3. PDU de-energises the HCR150 coil

This costs one PDU channel for the alternator excite feed, counted in 6.44 above.
Set the delay from a measured field-collapse time on the bench, not a guess.

The mechanical master cutoff in the trunk gets no such courtesy, which is the
normal trade for a crash switch - that is what the alternator's own load-dump
rating is for.

---

## 6.46 Is the PDU worth buying at all? - OPEN DECISION

Raised by Daniel 2026-09-22, immediately after 6.44 settled on option B. The
question is fair and the answer is not obviously yes. **Do not order a PMU-16
until this is closed.**

### What changed

Under option B the PDU keeps both junction blocks alive and only feeds buses. So
it is no longer replacing the cabin's fusing - it is replacing **J/B No.2 alone**,
plus doing some logic. That is a much smaller job than the architecture in 3.1 and
6.38 was written for.

### What is actually kept vs deleted

| | Fuses | Relays |
|---|---|---|
| **J/B No.1** - kept, untouched | 10 (ECU-IG 15, WIPER 20, GAUGE 15, TURN 10, IGN 7.5, CIG/RADIO 15, STOP 15, ECU-B 15, TAIL 15, DEFOGGER 30) | 4 (taillight, defogger, turn flasher, integration) |
| **R/B No.2** - kept | 1 (POWER 30) | 1 (power main) |
| **R/B No.3** - kept | - | 1 (fog) |
| **R/B No.4** - kept | 3 (HEATER 40, A/C 10, FR FOG 20) | 1 heater + OEM starter relay (isolated) |
| **Totals kept** | **14** | **7** |
| **J/B No.2** - deleted | 5 (HEAD LH 15, HEAD RH 15, HAZ-HORN 15, DOME 20, RTR 30) | headlight + rad fan coil, both now unused |

So the car keeps 14 factory fuses and 7 factory relays, already wired, at zero
labour. The PDU's entire fusing job is the five J/B No.2 circuits.

### The two paths, costed

**PMU-16: $1,499** (ECUMaster USA, 2026-09-22; 39-pin connector and terminals
included, USB-to-CAN programming cable extra).

**Relays and fuses instead:**

| Need | Part | Note |
|---|---|---|
| HEAD LH, HEAD RH, RTR, horn | 4 micro ISO relays | 8 owned, 6 already assigned to k_efi/k_etb/k_fp/k_fan/k_fan2/k_str, so buy ~2-3 more |
| DOME, AM1, AM2, 3 CAN device feeds | fuse ways only | AM1/AM2 were always plain fused feeds in 3.1 |
| 10 new fuse ways | second fuse block | TE `2141029-1` is full at F1-F13 |
| Pi hold after key-off | **CSB3 low-side** holding a relay coil | |
| Kill relay coil | **CSB3 low-side** | |
| Alternator excite drop | **CSB3 low-side** | |

Order of **$150-250** against $1,499.

### The CSB3 is the hidden reason this works

The logic the PDU was going to do can mostly go to the CSB3's four low-side
outputs, which are presently unassigned. The ECU commands them over CAN on 0x643,
and the ECU is alive throughout key-off because of its own hold power.

**They are exactly used up, with nothing spare:**

| L-channel | Job |
|---|---|
| L1 | Pi hold relay |
| L2 | Kill relay coil |
| L3 | Alternator excite drop |
| L4 | Oil pressure lamp (6.43 / ClusterLED) |

If a fifth low-side job appears, something has to move - most likely the oil lamp,
which the TrackCluster could drive itself since it is already a CAN node.

### Check on option C as well

Deleting both junction blocks means re-homing 14 fuses and 7 relays. After the
three CAN devices, AM-bus and sequencing loads, that does **not** fit in one
PMU-16 either. Option C is a two-unit decision, not a one-unit decision.

### What the money actually buys

Keep the PDU for: per-channel current monitoring on CAN, resettable electronic
fusing, soft-start on the retract motors and headlights, load shedding during
crank, sequencing without spending CSB3 channels, and four spare outputs.

Drop the PDU for: about $1,300, one fewer CAN node to configure, and failure modes
a person can diagnose with a test light instead of a laptop.

### Recommendation

**Daniel's instinct is right.** With both junction blocks staying, a PMU-16 is
poor value - it is a sixteen-channel device doing five circuits and some timing,
and the timing has a free home in the CSB3. The honest case for buying it is
wanting the diagnostics, or intending to go to option C later.

Recommend dropping it unless the current monitoring is something he actively
wants. If it is dropped, 6.38, 6.44 and 6.45 all need rewriting - the cluster,
CSB3 and Pi feeds move to fused relay outputs, and the kill sequence moves to the
CSB3.

### CLOSED 2026-09-22 - dropped

Daniel's answer: no PDU. The replacement architecture is **6.48**.

---

## 6.47 Is there a bigger PDU that makes option C worth it? - surveyed, no

Asked by Daniel 2026-09-22 as the follow-up to 6.46. Prices and specs checked the
same day.

### What option C would actually need

Deleting both junction blocks means re-homing everything in 6.46's kept table,
plus what J/B No.2 already lost, plus the devices:

| | Outputs |
|---|---|
| J/B No.1 fuses | 10 |
| R/B No.2 POWER, R/B No.4 HEATER / A/C / FR FOG | 4 |
| J/B No.2 circuits | 5 |
| TrackCluster, CSB3, RealDash Pi | 3 |
| Alternator excite, kill | 2 |
| **Total** | **~24** |

With at least three channels able to carry 30-40 A: HEATER 40, DEFOGGER 30, RTR 30.

### The market

| Unit | Outputs | Max per channel | Price USD | Verdict |
|---|---|---|---|---|
| ECUMaster PMU-16 | 16 - 10 x 25 A, 6 x 15 A, 150 A total | 25 A | **1,499** | Too few for C |
| Haltech PD16 | 16 - 10 high-side, 2 half-bridge, 4 x 25 A, 120 A | 25 A | **1,099** | **Disqualified** - runs only with a Haltech Elite or Nexus ECU, not standalone. We are on a Link G4X |
| Racepak SmartWire | ~30 (per the SW30 designation; per-channel split not confirmed) | not confirmed | **1,750** | Closest fit. Sold explicitly as a fuse-panel-and-relay replacement |
| MoTeC PDM32 | 32 - 8 x 20 A, 24 x 8 A | 20 A | **5,165** | Price absurd here, and **no channel reaches 25 A** |
| 2 x PMU-16 | 32, 300 A | 25 A | **2,998** | Works. Silly |

### Two things kill option C regardless of which unit is bought

**1. The blower does not fit any of them.** R/B No.4's HEATER circuit is 40 A. The
best channel in the table is 25 A. So the blower stays on a relay and a fuse
whatever is bought, which means **R/B No.4 cannot actually be deleted** - and
DEFOGGER 30 A and RTR 30 A need paralleled channels on every unit listed.

**2. The integration relay.** J/B No.1's integration relay runs intermittent
wipers, courtesy-light delay and the seatbelt / key warnings. Reproducing it means
feeding door switches, the seatbelt switch and the key switch into the PDM as
inputs, then writing the logic. That is more wires going **into** the dash, which
is the opposite of the goal, and it is config work on top.

### Conclusion

**No, there is no PDU that makes deleting both junction blocks worth it on this
car.** The cheapest unit with the channel count costs $1,750, still cannot run the
blower, still leaves R/B No.4 in place, and asks for new dash inputs to replace a
relay that already works.

6.46's recommendation stands, and this strengthens it: relays, a second fuse block
and the CSB3's low-side outputs.

### If the monitoring is what Daniel actually wants

That was the one real argument for a PDU, and it can be had for about $60.

The CSB3 has **eight analog inputs and only A1 and A2 are used**. Hall-effect
current sensors on the circuits worth watching - fuel pump, fans, EPS, headlights,
blower, defogger - feed A3 to A8, go out on CAN, and land on RealDash and the
TrackCluster, both already CAN nodes.

Six monitored circuits, no new module, no new CAN node, and it uses inputs that
are already paid for and currently idle.

---

## 6.48 NO PDU, and no added logic

**Settled with Daniel 2026-09-22.** Rewritten the same day after he cut the scope:
the first draft of this section invented a shutdown system nobody asked for.

Two decisions:

1. **The PMU-16 is not being bought.** Reasoning in 6.46 and 6.47.
2. **The only logic on this car is the ECU's own hold power.** Everything else the
   first draft added - device hold relays, a PDU-controlled battery kill,
   alternator excite sequencing, a permanently live CSB3 - is **withdrawn**.

This supersedes the PMU parts of **6.38** and **6.44**, and **withdraws the
electronic kill in 6.43 and 6.45** entirely.

### What the five ex-J/B2 circuits get

| Circuit | Source |
|---|---|
| HEAD LH 15 A | relay + fuse -> J/B2 2A-3 / 2D-2 |
| HEAD RH 15 A | relay + fuse -> J/B2 2A-6 / 2D-6 |
| RTR 30 A | relay + fuse -> 2E-2 |
| HAZ-HORN 15 A | fuse -> 2E-3, plus a horn relay if the car has none |
| DOME 20 A | fuse only, always-hot -> 2E-4 |

A second fuse block in the glove box, because TE `2141029-1` is full at F1-F13.

### CAN devices - ordinary switched feeds

CSB3, TrackCluster and RealDash Pi each get **a fuse off ignition-switched 12 V**.
No relay to hold them, no permanent feed, nothing clever. They come up with the key
and die with it.

**The CSB3 is not always live.** That idea existed only to serve the kill sequence,
and there is no kill sequence.

**The Pi is an info display and nothing more.** It has no role in any shutdown. Its
SD card is exposed to hard power-off the same way any carputer's is; that is a known
and accepted trade, not a problem to engineer around here.

### Battery kill - manual switch, full stop

A **manual master cutoff in the trunk**, already on the buy list. No relay, no ECU
involvement, no sequencing.

The HCR150 goes back to being just the EPS pump relay. Two are owned, one is used,
one is spare for anything.

One practical note, offered once: opening a master switch with the engine running
is a load dump on the alternator. Most motorsport master switches carry an
auxiliary terminal for exactly this - it kills the alternator excite as the main
contacts open. Worth specifying when the switch is bought. Shutting the engine off
first also solves it.

### ECU hold power - unchanged, and the only logic

Exactly as already built: `k_efi` coil positive on permanent battery through F12
5 A, coil negative on ECU **Aux 6 / A28**. The ECU holds its own relay after key-off
to park the electronic throttle and save, then releases.

Self-contained in the ECU. Nothing else participates and nothing else needs to know.

### CSB3 low-side outputs

All four are **free again**. The only candidate is the oil pressure lamp (6.43 /
ClusterLED). Three spare.

### Relay and fuse count

Relays: HEAD LH, HEAD RH, RTR, and a horn relay if needed - **3 to 4 micro ISO**.
Eight are owned with six assigned to `k_efi`, `k_etb`, `k_fp`, `k_fan`, `k_fan2`
and `k_str`, so **buy 2 spare** and the count works.

Fuse ways: HEAD LH 15, HEAD RH 15, HAZ-HORN 15, DOME 20, RTR 30, CSB3 5, cluster
10, Pi 15 - **8 ways, so a 12-way second block** with room left.

### What DOES change in the cabin

Correcting an overstatement in the first draft of this section. The dash branch
wiring is untouched, but **power and ground delivery to the junction blocks is
entirely new**, and that is real cabin work:

| New injection | Where |
|---|---|
| Always-hot | J/B1 `1I-1` |
| AM1 40 A | `IE1-10` |
| AM2 30 A | `IE1-17` |
| POWER feed | R/B No.2 fuse input |
| HEATER feed | R/B No.4 fuse input |
| Ground strap | left-kick `ID` stud |
| Ground | new stud at the R/B No.4 set bolt |

Seven new terminations in the cabin, from a PDB that did not exist before, on a
battery that is now in the trunk. What is *not* changing is anything downstream of
a junction block fuse.

### Monitoring, if wanted later

Per 6.47: hall current sensors into CSB3 analog inputs A3-A8, which are idle. About
$60, no new module. Unrelated to any of the above.

### Open

- Confirm whether the car already has a horn relay.
- Pick the 12-way second fuse block.
- Specify a master cutoff with an alternator-excite terminal.

---

## 6.49 Parts lists that do not double up (2026-09-22)

Daniel: *"Make sure every harness uses a parts list that doesn't double up on
devices."* Three new audits were written to answer it. They found four real
defects, not one.

### What was wrong

| # | Defect | Effect on the buy list |
|---|---|---|
| 1 | 118 bulkhead cavities claimed a contact **and** a sealing plug | ~70 plugs ordered for cavities that already have a pin. The app hid it - assigning one clears the other - so only the JSON showed it |
| 2 | A-ECU drew all six relays as the generic `(OEM block, 5-way)` placeholder while B-ECU already had the real TE parts | A-ECU is read first, so the relays fell out of the count entirely and were being hand-patched back through `EXTRA` |
| 3 | `cp_rly_cod` had **two different part numbers** - `6-1419137-4` in B-ECU, `5-1393292-8` in EngineRoom-C | The make-contact relay was sitting under the id used for the changeover one. Order from the wrong drawing and the fan relay has no 87a |
| 4 | `buildlist.py` walked `wires` only | WheelSpeed has no `wires` element at all - every conductor is a cable core or shield - so the **whole loom** was missing from the build list, and three A-engine shielded runs with it. 254 -> 283 wires |

Defect 4 is the dangerous one. The same blind spot in the cavity pass would have
put sealing plugs into seven live bulkhead cavities.

### Relays, verified on te.com 2026-09-22

| Part | Contact | Coil | Rating | Suppression |
|---|---|---|---|---|
| `5-1393292-8` | 1 Form A, make | 12 V | 25 A | Diode |
| `6-1419137-4` | 1 Form C, changeover | 12 V | 25 A | Diode |
| `4-1904124-2` | 1 Form A, make | 12 V, 119 R, 1.42 W | 25 A | **not stated by TE - UNVERIFIED** |

`4-1904124-2` is used for `k_etb` and `k_str`. Neither drives an inductive load
back into a low-side ECU output that needs the diode, so it is not urgent, but
the description now says UNVERIFIED rather than "resistor suppressed".

### RADLOK firewall pass-through - part number is wrong

The battery feed-through was drawn as one part number, `RL00571-35`, used twice,
described as a "bulkhead pair". Checked against Amphenol:

- The RADLOK catalogue lists **RL00571-16** and **RL00571-25** for the 5.7 mm
  RADSOK contact. The trailing number is the cable size in mm2. **There is no -35.**
- `RL00571-25` is a **cable-mount receptacle**, one piece. Not a pair, and not a
  panel mount. The mating half is a different part number.
- 5.7 mm RADSOK is rated **120 A**.
- The harness calls for **2 AWG**, which is **33.6 mm2**. It will not fit a 25 mm2
  connector. 25 mm2 is about 3 AWG.

The four connectors now carry four distinct `TBD ...` parts with that text in the
description, so the count is honest and nobody orders off a guess. **No
replacement part number has been invented.**

### Bulkhead cavities wired on one side only

`audit_bulkhead_pairs.py` is new. A bulkhead cavity must be wired on both halves
or neither, or the circuit dead-ends in the connector. Seven are one-sided:

| Cavity | Signal | Verdict |
|---|---|---|
| `bh_a_fw` c10 | ECU-A A23 (WSS FL) | known 6.41 loom-crossing violation |
| `bh_a_fw` c12 | ECU-B B21 (WSS FR) | known 6.41 loom-crossing violation |
| `bh_b_fw` c13 | ECU-A A27 (MRS speed) | known 6.41 loom-crossing violation |
| `bh_b_fw` c14 | "spare (size 16)" | known 6.41 loom-crossing violation |
| `bh_a_eng` c33 | Crank VR screen | **open - the screen lands in the bulkhead and stops** |
| `bh_a_eng` c34 | Cam Hall screen | **open - same** |
| `bh_a_eng` c35 | Knock 1 screen | **open - same** |

The first four disappear when 6.41 moves those wires out of bulkheads A and B.
The three screens do not. 6.32 gave each one a dedicated bulkhead pin, but the
cabin side was never wired, so today they terminate nowhere. Either wire
`bh_a_fw` c33-c35 through to the cabin shield splice, or drop the three pins and
let the screens share the existing single drain on c1.

### Rules now enforced

See `docs/harness/README.md` -> Parts rules. `check_all.py` runs the lot.

### Open

All three closed the same day:

- ~~Pick the real RADLOK part numbers.~~ **Closed, see 6.50.** Sized on current
  instead of guessed: 1/0 cable and RADLOK 8.0.
- ~~Confirm `4-1904124-2` coil suppression.~~ **Closed.** Daniel: the ECU I/O and
  most relays carry their own suppression, so it does not matter. What does
  matter is carrying over filtering the **OEM** fitted externally - see 6.51.
- ~~Decide the crank / cam / knock screen termination.~~ **Not a decision - it was
  already settled** in 6.27 rule 5 and 6.32. I raised it as open because
  SHIELD-RULES.md lived only in the claude.ai project and nothing in the repo
  checked it. See 6.50.

---

## 6.50 Shield rules, enforced — and why they kept getting re-asked (2026-09-22)

Daniel: *"Refer to my previous guidance regarding passing Shields through the
bulkheads to the ECU. This has been discussed a number of times. You need to keep
better track of rules like this."*

Fair. The rules were settled in 6.27 / 6.30 / 6.31 / 6.32 and summarised in a
`SHIELD-RULES.md` that lived **only in the claude.ai project, not the repo**.
Nothing in the pipeline checked them, so a half-finished migration survived and
got written up as an open question instead of a defect.

### The fix, in two parts

1. **`docs/SHIELD-RULES.md`** is now in the repo, next to the plan.
2. **`docs/harness/audit_shields.py`** enforces four of the five rules as a hard
   gate in `check_all.py`. Break one and the build fails.

| Rule | Checked? |
|---|---|
| R1 never connected at the device end | yes |
| R2 terminates at the ECU end only, and does reach it | yes |
| R3 no drain on a connector shell, except the VR enclosures | yes |
| R4 cable, not a wire, until the ECU | no — a modelling convention the schema cannot express |
| R5 crosses a bulkhead on its own pin, wired on **both** halves | yes |

The audit has to learn two things the schema does not say: a `dm_*`
cross-reference dummy is the same electrical node as the connector it names, and
all shells on one VR conditioner enclosure are one node (6.30). Without those it
false-flags the entire wheel-speed loom.

### What it found immediately

6.32 was half applied. The crank, cam and knock screens landed on their own pins
on the **engine** half of bulkhead A — c33, c34, c35 — and **nothing on the cabin
half**. So the dedicated pins dead-ended inside the connector and all three
screens were still travelling on the old shared c1 drain.

6.32 first choice is one pin per screen whenever the pins exist, and bulkhead A
has 16 free pairs, so the migration is now finished rather than rolled back:

```
  sensor ──(floats)══ cable screen ══ bh_a_eng c33/34/35
                                          │  (own pin, both halves)
                      bh_a_fw c33/34/35 ──┘
                                          └── sp_shield_cab ── ECU-A A7
                                                            └─ ECU-B B17
```

| Change | |
|---|---|
| **+** `w_shc_crank` / `_cam` / `_knock1` | `bh_a_fw` c33/c34/c35 → `sp_shield_cab` |
| **−** `w_sh_crank` / `_cam` / `_knock1` | jumpers to the engine-bay collector |
| **−** `sp_shield_eng` | collector splice, now empty |
| **−** `w_drain_bh_c`, `w_drain_bh_e` | the shared c1 drain — both halves of c1 are spare |

Each screen now floats at the sensor, crosses on its own pin wired both sides,
and terminates exactly once, at the ECU.

## 6.51 Firewall heavy-DC feed-through, sized properly (2026-09-22)

Daniel: *"Choose for me using current capacity and deciding wire size based on
that length."*

**What crosses.** The positive runs trunk battery → cabin PDB → firewall →
starter B+, and the alternator lands on that same starter post, so the full
charge current comes back through this one crossing. The negative is a dedicated
return from the engine block.

- Continuous design case: **160 A** (alternator at rating)
- Peak design case: **~300 A for a few seconds** (cranking a 2.2 L four)

**Wire size, from the length.** ~18 ft each way, so ~36 ft round trip:

| Case | 2 AWG | **1/0** | 2/0 |
|---|---|---|---|
| 160 A continuous | 0.90 V | **0.57 V (4%)** | 0.45 V |
| ~300 A cranking | 1.69 V (**13%**) | **1.06 V (8.4%)** | 0.84 V |

2 AWG blows past the 10% a starter circuit is normally held to. 2/0 buys 0.2 V
for a lot more money and a much worse bend radius. **1/0 (50 mm²)**, which is
exactly the RADLOK 8.0 cable size.

**Connector.** Three pieces per polarity — the feed-through lives in the
firewall, a cable connector plugs onto each side:

| Piece | Part | Qty |
|---|---|---|
| Feed-through, positive | `RL9080-301-F1RE` — 8.0 mm RADLOK, panel mount, pin both sides, 200 A / 1 kV, IP40 mated, red | 1 |
| Feed-through, negative | `RL9080-301-F1` — same, black | 1 |
| Cable connector, positive | `RL00801-50RE` — female, 200 A, 50 mm², red | 2 |
| Cable connector, negative | `RL00801-50BK` — same, black | 2 |

200 A continuous gives 25% headroom on the alternator case, and a connector of
this class shrugs off a few seconds of cranking. The `-303` nickel variant is
discontinued; RS names `-301` as its replacement.

H1–H4, H6 and H7 go to 1/0. H5 (alternator B+ to starter post) stays 2 AWG — it
is a short engine-bay jumper that never crosses the firewall.

## 6.52 OEM filtering carried into our drawings (2026-09-22)

Daniel: *"Suppression isn't a big deal because many of the ECU IO have their own
built-in suppression or flywheeled pins... Just make sure that any circuits in the
OEM wiring diagrams that contain filtering diodes or capacitors specify those in
our diagrams so I can replace them where necessary only where external filtering
stuff was used on the OEM."*

Read of the EWD snips in `docs/electrical/ewd-snips`:

| EWD page | What is in it | Verdict |
|---|---|---|
| p.19 J/B No.1 inner circuit | **one 3-terminal diode**, two diodes with a common cathode on pin 2 | Inside a block we **keep**. Nothing to build — but do not inject power in a way that bypasses or backfeeds it |
| p.21 J/B No.2 inner circuit | nothing — relays and fuses only | — |
| p.22 J/B No.3 inner circuit | nothing — pure junction block | — |
| p.46 Power source | nothing | — |
| p.48 Starting and ignition | diode inside the **S2 start injector time switch**, between the STJ and STA coils | Deleted with the cold-start injector |
| p.52 Charging | the **C12 charge lamp**, pin 9 (IG, B-O) to pin 8 (alt L, Y) | **This one matters — see below** |

**No capacitors anywhere in the snipped pages.**

### The charge lamp is not an indicator

It is the alternator's pre-excitation path: IG → bulb → L terminal → field. A
3.4 W bulb passes roughly **250 mA** at 13.8 V. The LED replacing it passes about
**20 mA** — an order of magnitude less — and many IC regulators will not
self-excite on that, so the car would not start charging until it was revved.

Added to `ST185-ClusterLED`: **`r_chg_excite`, 56 Ω 5 W, in parallel with the
charge LED**, carrying the current the bulb used to. It only dissipates while the
lamp condition is true — once charging, both ends sit at ~14 V. The value is the
bulb-equivalent starting point and is marked **CONFIRM against the fitted
alternator**; it is the one number here that depends on a part not yet bench-tested.

The same drawing now carries a schematic note listing all of the above, so it
travels with the diagram rather than living in a commit message.

### Bonus, off p.24 (R/B No.5)

**The car already has a horn relay**, in the engine-compartment front-right relay
block. That closes a 6.48 open item.

## 6.53 The EPS pump is one part, not a Group (2026-09-22)

Daniel: *"Why create a group? Just create a part with the correct number of total
pins (both used and not used) and give the pins specific labels so I know which
connector is which on EPS housing."*

Right, and it sidesteps the fact that the MCP tools cannot create Groups anyway.
`mrs_pwr`, `mrs_ctrl` and `mrs_en` are now one 10-pin connector, `mrs_eps`, with
the housing letter in every designation and every signal:

| Pin | Housing | Signal |
|---|---|---|
| A-1 | `90980-12068` 2-way, main power, 8 AWG | +12V from `k_eps` 87, passenger fender |
| A-2 | same | GND, 8 AWG to engine block / EB |
| B-1 | `90980-10897` 6-way, signal, pigtail `82998-12440` | not used |
| B-2 | same | **SPD Out** — speed pulse → ECU-A A27 |
| B-3 … B-5 | same | not used |
| B-6 | same | relay request out — **not wired**, 6.16 moved the trigger to the ECU (Ign 6 / B12) |
| C-1 | `90980-10942` 2-way, ignition | IG-switched, F13 7.5 A — pump enable |
| C-2 | same | not used |

Five wires re-pointed, no net changed. `gp_mrs_ehps` dropped. `k_eps` stays
separate — it is an HCR150 bolted beside the pump, not part of it.

## 6.54 Finish pass - contact limits, fusing and feeds (2026-09-25)

Daniel's rulings applied in one pass across all nine looms. Every wire is now
inside its contact's rated range and every fuse sits on a wire sized for it.

### Relays - plug-in Maxi ISO F7 on the VCF7 socket

The Micro ISO socket contact `160927-4` stops at 14 AWG, too small for the 12 and
8 AWG load wires. Load relays move to TE F7 relays from the on-hand sheet, on
socket `1393310-4`:

| Relay | Part | Load contacts (30 / 87) | Coil contacts (85 / 86) |
|---|---|---|---|
| `k_efi`, `k_fp` | `1-1414147-0` (680 ohm, owned 3) | `280756-4`, 12-10 AWG | `42281-1`, 18-14 AWG |
| `k_str` | `1-1393304-0` (560 ohm, owned 2) | `280756-4` | `42281-1` |
| `k_fan` | `1-1393304-0` | `280755-4`, 10-8 AWG | `42281-1` |
| `k_fan2` | `7-1904094-9` (diode, cathode on 86, buy 1) | `280755-4` | `42281-1` |

Cavity 87a is gone (the F7 relays are 1 Form A). Coil wires are 18 AWG. `k_etb`
stays on the Micro ISO socket, its wires fit.

### High-current fuse block HCFB

The MFINITY module `2141029-1` takes 30 A mini fuses at most, and the total feed
exceeded its bus, so the 60 A EPS fuse and both fan fuses leave it. New block in
the glove box: Eaton Bussmann LMI (`LMI1-M-1-1` input, 4x `LMI1-M-1-0`, busbar),
input on an M8 stud from the PDB, 4 AWG.

| Position | Fuse | Load | Wire |
|---|---|---|---|
| H1 | 50 A AMI | FB1 IN (permanent bus) | 10 AWG |
| H2 | 40 A AMI | `k_fan` 30 | 8 AWG |
| H3 | 30 A AMI | `k_fan2` 30 | 8 AWG |
| H4 | 60 A AMI | `k_eps` 30 (loom C) | 8 AWG |

FB1 bus is split: IN feeds F1-F4, F8, F12, F13 (permanent); SW IN (`c15`) takes
the EFI main relay 87 (`w77`, 10 AWG) and feeds F9-F11. That makes F9 the only
feed into `sp_sw12`. Bus feed contacts `1-1355844-1` (4-6 mm2). F2 (fuel pump) is
25 A on 12 AWG, F3 (ETB) is 10 A, F10 feeds the COP bank and F11 the injector bank.
`w65` (unfused battery into `sp_12v`) is deleted. `w_pdb_jb1` (6 AWG) is fused
60 A at the PDB.

### Fans, grounds, splices

- Fan power and ground each get a 1-way DTHD plug `DTHD06-1-8S` with size 8
  contacts `0462-203-08141` (owned 9), which take 8 AWG.
- The doubled fan / EPS grounds on loom C are drawn once.
- `sp_chassis_eng` takes the larger size (crimp splice 10-6, `w_eng_gnd` 10 AWG),
  and both 5 V rail legs are 18 AWG.
- Fuel pump ground lands on its own trunk stud `t_trunk_fp_gnd`, not the ECU
  chassis splice.
- ClusterLED: one IG tap off C12-9 feeds `sp_led_12v`; the oil LED sinks on CSB3
  L4 (`csb3io` c26).
- Cam pull-up colours: +8 V side Orange/White, signal side Blue (same as the cam
  signal).

### Working assumptions (best evidence, confirm at the car)

These close the old unverified items. Each one is also written into the part or
cavity it affects.

| Item | Assumption |
|---|---|
| COP plug `90980-11885` | 1 +B, 2 IGF (not used), 3 IGT, 4 GND (Denso 4-pin pattern) |
| Turbo speed sensor | Garrett 781328-type; pin 1 is +5 V from the ECU rail (the kit's 12 V lead is for its gauge only) |
| Toyota TS 090 terminals | Sumitomo `8100-0461`, 0.5-1.25 mm2 (20-16 AWG), family match to each OEM housing |
| Starter S terminal | 6.3 mm single spade |
| Stud sizes | Ground studs M6 (including the trunk fuel-pump stud), PDB and HCFB input M8, HCR 150 load studs M6 (TE datasheet) |
| FB1 `2141029-1` | Bus can be split into IN and SW IN; total rating spec not found |
| LMI busbar | `B109-7046-5` |
| ETB contacts | Come in the Bosch `D 261 205 358-01` kit |
| OEM blocks | Existing OEM connectors are kept, not rebuilt |
| MR-S EHPS power terminal | Takes 8 AWG |
| ClusterLED | Common return on OEM ground ID, left kick panel; current-limit resistors are on the LED board |
| Binder M8 VRC leads | Cable plugs `99 3363 100 04` / `99 3362 100 04` (0.14-0.5 mm2, cable OD 4.0-5.5 mm) mate the panel parts in `docs/enclosures/vr-conditioner-bom.csv` |

### Parts library and connector images

- Every part in the nine looms is now in the shared ST185 Parts Library (5LO8), matched by part number. The Toyota TS contact is `8100-0461`, updated in place.
- Shielded cable parts carry their own part numbers (`GENERIC SHLD CABLE 1C 20AWG BLU`, `... 1C 20AWG VIO`, `... 2C TP 20AWG`, `... 3C 20AWG`, `... 4C 20AWG`) instead of a shared `(generic)`, so the library can hold one of each. They are still generic cable per 6.24.
- EngineRoom-C carries one RADLOK part per colour (`RL00801-50BK`, `RL00801-50RE`), used on both sides of the feed-through. Qty 2 each.
- Every connector part has an image. Manufacturer or distributor photos are linked by URL (TE, Mouser, Bosch and Toyota vendors). OEM, TBD and cross-reference parts, which have no catalogue photo, use representative drawings in `docs/harness/part-images/`. Those drawings are labelled as drawings, not photos.
- Shared-family photos: the three F7 relays share TE's Power Relay F7 family photo. `4-1904124-2` uses the Micro ISO photo from `9-1904105-7`. `HD36-24-33SE` uses the `HD36-24-33SN` photo (same shell, N key). All four 8STA parts use Mouser's series photo.
