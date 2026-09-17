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
