# Reconciliation rules — binding on every agent

Agent-agnostic. Claude Code, Cursor, Codex, or any other tool: these apply. The
per-agent rule files (`.cursor/rules/`, `.claude/rules/`, `AGENTS.md`) point here for the
**procedure**. The rule statements themselves (what Daniel decided, dated, R1-R132) are
owned by `docs/harness/redesign/DECISIONS.md` "Binding rules from Daniel"; this file says
how to apply them and which surfaces must agree. Where the two disagree, `DECISIONS.md` wins.

Three rules. Rules 1 and 2 exist because this project has repeatedly drifted: a change
landed in one document and its siblings silently disagreed for weeks. Rule 3 is how the
ECU harness is split into files, and this file owns its wording.

---

## Rule 1 — Wiring: reconcile ALL wiring documents, not just the one you touched

**Trigger:** any change to any wiring document, diagram, harness file, pinout, or BOM.

**Requirement:** before the change is final, check it against the source-of-truth chain
**and** against every other wiring surface listed below — including the ones you did not
edit. They must all agree. A change that leaves two documents disagreeing is not done.

### Source-of-truth chain

```
docs/harness/wirelist/*-wirelist.csv   wiring SoT since R206: every wire, pin, splice, end, mate, net
      |
      +-- sot/channels.csv             ECU channel settings; wirelist.py --check compares its pins both ways
      +-- docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md
      |     device pin, pin name, whether that device gets a shield
      +-- XTREMEX-IO-TABLE.html        visual face; sync_io_table.py --check gates it
      +-- docs/harness/rebuild/*.harness   the physical looms  <- what gets built
              |
              +-- harness.design app copy   mirror - never edit as source
```

New wiring facts go into the wire list row **first** (R206; before the switch: `sot/channels.csv`, Daniel 2026-09-25), then `channels.csv`
(ECU channel settings and pin), the IO table and the looms follow. Device pin, pin name, and whether that device gets a
shield go into `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`. One shield flag
per device or sensor, not per connector pin and not per wire. Which ECU pin a
device wire lands on is owned by the ECU. If anything disagrees with the wire list on
a pin, the other thing is wrong and gets corrected - never the reverse.
`python docs/harness/check_all.py` enforces the whole chain and must pass before
every commit.

### ECU pins: check the Quick Start Guide and the plug-in guides (R212)

A wire on an ECU pin (plugs A / B / C) is also checked against the Link G4X Quick Start Guide and the G4X plug-in
(wire-in) guides (the plug-in guide wins for special circuits and pin modes): pin function and mode, what the pin
may connect to, current limits, wire gauge. `cleanroom/ecu_rules.py`, run by `cleanroom/wirelist.py --check`, fails
on any far end the pin's class does not allow (R212), any ground that breaks the ground classes (R213, R216), any
relay driven the wrong way (R219);
known violations waiting for the wiring fix are in `ecu_rules.PENDING`.

### Every wiring surface that must agree

| Surface | Role |
|---|---|
| `docs/harness/wirelist/*-wirelist.csv` | Wiring SoT (R206) |
| `sot/channels.csv` | ECU channel settings; pins checked against the lists |
| `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` | Device pin, pin name, whether that device gets a shield (one flag per device, never per pin or wire) |
| `XTREMEX-IO-TABLE.html` | Visual face of the ECU SoT, with a generated pin map |
| `docs/harness/rebuild/ST185-ECU-cabin.harness` | The ECU harness, cabin side (Rule 3): ECU plugs A, B, C to the cabin half of the DRB102 bulkhead, the relay coil wires (broken off to the box), the APS pedal, the wheel-speed spurs, fuel level, the ECU splice point; drawn by our own generator, the file is its parts / cavity data |
| `docs/harness/rebuild/ST185-CabinPower.harness` | Glove-box POWER + LOGIC fuse boxes (DECISIONS R75, CAD rev 5) with the ECU-switched relays seated in them (all but `k_fp`), battery feed (non-ECU) |
| `docs/harness/rebuild/ST185-CSB3.harness` | ECUMaster CSB3 plug and switch inputs (non-ECU) |
| `docs/harness/rebuild/ST185-ECU-engine.harness` | The ECU harness, engine side (Rule 3): the engine half of the DRB102 to every engine device the ECU drives or reads, the ETB included |
| `docs/harness/rebuild/ST185-CAN.harness` | CAN backbone - the only drawing with CAN H/L |
| `docs/harness/rebuild/ST185-EngineRoom-C.harness` | Loom C engine room, no bulkhead |
| `docs/harness/rebuild/ST185-WheelSpeed-Front.harness` / `-Rear.harness` | Wheel-speed Y harnesses to VRC endpoints and `IX_WS_FRONT` / `IX_WS_REAR` |
| `docs/harness/rebuild/ST185-RearFuel.harness` | Fuel level sender behind `IX_FUEL_LVL`; fuel pump + ground, fed from `k_fp` (HeavyDC battery relay block) |
| `docs/harness/interfaces.json` | Ownership registry: interfaces, endpoints, flying leads, references |
| `docs/harness/rebuild/ST185-ClusterLED.harness` | Cluster warning LEDs |
| `docs/harness/rebuild/ST185-AntiTheft.harness` | Anti-theft |
| `docs/harness/rebuild/ST185-RearLights.harness` | Rear lights: J/B No.1 / S9 feeds to the rear lamps, reverse from `k_rev` |
| `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` | OEM landing facts and EWD citations for every ex-J/B2 / R/B load (§5.4); the wire lists own the wiring |
| `docs/harness/NEED-TO-BUY.md` | Generated - re-run `buylist.py` |
| `docs/harness/redesign/DECISIONS.md` | The binding rules (R1-R132) and the dated decisions |
| `docs/SHIELD-RULES.md` | Shield rules, enforced by the audits |
| `docs/sourcing/te-on-hand-bom.csv` | Parts already owned - check before speccing anything new |

The ECU harness is two files, cabin and engine (Rule 3). Every cavity on the bulkhead's cabin
half mates the same cavity on its engine half. `audit_mating.py`, `audit_pin_names.py` and
`validate_breaks.py` check that.

The frozen pre-split baseline and `verify_rebuild.py` were retired on 2026-09-27;
`verify_connectivity.py` replaced them. Dated audit notes and one-shot fix scripts
are not authoritative.

Generated files are never hand-edited — re-run their script.

### No factory engine-bay wire is reused

Rule **R11** in `DECISIONS.md` (Daniel, 2026-10-04 / 2026-10-12). Applied here: an
`oem_flying_lead` on an engine-bay harness (`EngineRoom-C`, `ECU-engine`,
`HeavyDC`) is a new-wire run to the device's own plug, never a splice into a factory lead;
`audit_dan_rules.py` D1 checks the registered method text.

---

## Rule 2 — CAN: any change on any device reconciles across all devices

**Trigger:** any change to CAN configuration on **any** device, in **any** repo.

**Requirement:** reconcile and verify against every other CAN participant before the change
is final. All of them, every time — not just the pair you happened to be working on.

### The participants

| Device | Where its config lives |
|---|---|
| **Link G4X XtremeX ECU** | `link_g4x_can_setup.json`, `link_g4x_can_setup.lcs`, `CANBUS-LINK-G4X-CONFIG.md` |
| **Center cluster (ESP32-P4)** | `center-cluster-esp32-p4` repo — `main/canbus.c` |
| **RealDash** | `link_g4x_realdash.xml`, `st185_dash.rd`, `REALDASH-LAYOUT.md`, `rd-build/` |
| **ECUMaster CAN Switchboard (CSB3)** | `ECUMASTER_SWITCHBOARD_SETUP.md` |
| **Link CAN-Lambda** | On the same bus — see bus facts below |

Shared contract documents that must also stay in step: `CAN-BUS-ID-ALLOCATION-TABLE.md`,
`CAN-BUS-MASTER-DESIGN.md`, `BENCH-TEST.md`, `bench/frames.py` (the cluster's
`CANBUS-ENCODE-DECODE-REFERENCE.html` lives only in the cluster repo - linked, never copied).

### Bus facts

- **Link CAN-Lambda is on CAN bus 1**, with everything else. It is not on a separate bus.
- **CAN bus 2 is not used.** Its ECU pins are therefore free and may be reassigned to
  whatever we need. Do not reserve them for CAN.
- Single bus, 1 Mbit/s.

### Authority order when two configs disagree

1. **Center cluster firmware as flashed** — highest. It is frozen.
2. PCLink CAN configuration on the ECU.
3. Everything else.

The cluster firmware being frozen means: when a conflict is found, the **other** device
changes. Reflashing the cluster is a last resort and needs explicit approval from Daniel —
never do it to make a mismatch go away.

### What "reconcile" means concretely

For every frame the change touches, confirm across all participants:

- frame ID
- byte offsets and field widths
- endianness (BigEndian unless a canonical doc says otherwise)
- scaling and offset
- units
- which device transmits and which receive

Record the outcome. If a mismatch is found and not fixed in the same pass, it gets written
down as an open item — never left silent.

---

## Rule 3 — the ECU harness: one cabin file, one engine file

**Daniel, 2026-10-19 (DECISIONS R220): loom A and loom B are one harness** - "they both come from
the same bulkhead". It replaces the 2026-09-28 connector-letter split (four files, crossovers a-c).

- **Two ECU harness files:** `ST185-ECU-cabin` (ECU plugs A, B and C to the cabin half of the
  DRB102 bulkhead, plus every cabin branch) and `ST185-ECU-engine` (the engine half of the
  bulkhead to every engine device the ECU drives or reads, the throttle body included). The
  letters A / B / C are the ECU's own plug names and stay on the pins; the ECU pin assignments
  never move (APS, wheel / vehicle speed and ETB pins are fixed by the G4X plug-in guide).
- **One bulkhead connector per side:** the receptacle `bh_fw` on ECU-cabin, the plug `bh_eng` on
  ECU-engine; cavities are assigned by device (R208, `docs/harness/DRB102-CAVITY-MAP.md`,
  generated by `cleanroom/bulkhead_assign.py`).
- **The ECU splice point:** every cabin power, ground and rail splice sits at one place by the
  ECU plugs. +5 V (A32) is two bussed DT plugs `BUS-5V` (12-way) and `BUS-5V-2` (8-way, linked);
  Gnd Out A24 and B22 are their own 12-way bussed DT plugs `BUS-GNDOUT-A` / `BUS-GNDOUT-B` (the
  two sensor grounds stay separate: no A24-B22 tie); +8 V, switched 12 V, the ECU A5 feed and the
  ECU power ground are soldered splices there (R169 parts: `DT06-12SA` / `DT04-12PA-P021`,
  `DT06-08SA` / `DT04-08PA-P021`, 13 A per pin). The ECU power ground splice joins A25, A34,
  B25, B34 only and runs one wire to the POWER box battery-negative bar (R216).
- **Splice sizing:** rule **R36** (combined gauge, Wire Barn calculator; not for drains, R30).
  Gate: `audit_cavity_parts.py` K3.
- **Connector substitution:** rule **R8** (complete matching set, datasheet part numbers). The
  pair is registered as an inline interface in `docs/harness/interfaces.json` and counted on
  the buy list.
- **No harness is drawn inside another.** A wire that runs between two harness files is drawn
  **broken off in both**, each section ending at a noted terminal that names the other file; a
  device is drawn once. Where that will not resolve, a connector pair where the wire leaves one
  harness and enters the other, noted in both. No cross-reference dummies. The pairs are
  registered in `docs/harness/interfaces.json` "breaks"; `validate_breaks.py` L6 / L7 enforce them.
- **Drawings:** the two ECU harness files are drawn by our own generator from the wire list
  (`"drawing": "own"` in `interfaces.json`, R220), not in the harness.design app, so the app's
  100-connection limit (R69) does not apply to them. Their `.harness` files stay as the parts /
  cavity data every data gate reads; the app-canvas geometry gates skip them.
- The ECUMaster CSB3 plug and its switch inputs are their own non-ECU harness, `ST185-CSB3`.
- The glove-box POWER + LOGIC fuse boxes and the battery feed ring are the non-ECU harness
  `ST185-CabinPower`. The fuel pump relay `k_fp` sits in the battery relay block in the trunk,
  drawn in `ST185-HeavyDC`; the pump run is `ST185-RearFuel`. The boxes live in that file only;
  every other file reaches it through broken-off pairs. The ECU-switched relays sit in the boxes
  and are drawn there; their ECU coil (85) wires stay on `ST185-ECU-cabin` and break off to the box.
- Every other loom stays as it is: `EngineRoom-C`, `CAN`, `ClusterLED`, `AntiTheft`,
  `WheelSpeed-Front` / `-Rear`, `RearFuel`, `HeavyDC`, `RearLights`.

**Enforced by** `docs/harness/validate_breaks.py` (E1 / E2: ECU-pin and bulkhead wires live on the
ECU harness files; L6 / L7: breaks and one element per drawing), a hard gate in `check_all.py`.

---

## Scope note

These rules cross repository boundaries. The cluster repo is checked out alongside this one
at `C:\projects\active\center-cluster-esp32-p4`, so references such as `main/canbus.c`
resolve there, not here. A CAN change in this repo that affects the cluster is not complete
until the cluster side is checked, even though it lives in a different repository.

The only center-cluster portion in this repo is the CAN node, plus power and
ground to the cluster. Interior cluster wiring lives only in the center
cluster repo. Do not add interior cluster circuits here.
