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
   REAR of car                                            ENGINE BAY
   (leftmost)                                             (far right)
  ┌──────────────────────────────────────────────────────────────────┐
  │  rear driver-side items        │  BH-A│BH-A │   engine bay       │  DRIVER
  │                       ┌──────┐ │  fw  │ eng │   driver-side      │  SIDE
  │                       │ ECU  │ │      │     │   items            │  (top)
  │  ─────────────────────│ A  B │─┤ face │face ├────────────────────│
  │                       └──────┘ │  ►   │  ◄  │                    │  PASSENGER
  │  rear passenger-side items     │  BH-B│BH-B │   engine bay       │  SIDE
  │                                │  fw  │ eng │   passenger-side   │  (bottom)
  └──────────────────────────────────────────────────────────────────┘
        left of centre ─┘
```

- **ECU A and B always adjacent**, placed **left of centre**.
- **Rear-of-car items** occupy the **leftmost** portion.
- **Driver side** in the **top half**, **passenger side** in the **bottom half**.
- **Bulkheads A and B near each other, to the right of the ECU.**
- **Engine-bay bulkhead halves immediately to their right, faces facing each other.**
- **Engine bay devices far right**, driver side top, passenger side bottom.

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
