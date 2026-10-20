# Reconciliation rules — binding on every agent

Agent-agnostic. Claude Code, Cursor, Codex, or any other tool: these apply. The
per-agent rule files (`.cursor/rules/`, `.claude/rules/`, `AGENTS.md`) point here for the
**procedure**. The rule statements themselves (what Daniel decided, dated) are
owned by `docs/harness/redesign/DECISIONS.md` "Binding rules B1-B30"; this file says
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
docs/harness/MASTER-wirelist.csv   the ONE wiring SoT (R221): every wire, pin, splice, end, mate, spare, of every harness
      |
      +-- sot/channels.csv             ECU channel settings; check_wiring.py compares its live pins both ways
      +-- docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md   device pin, pin name, whether that device gets a shield
      +-- XTREMEX-IO-TABLE.html        visual face of channels.csv (generated pin map)
      +-- docs/harness/drawings/       generated drawing sets  <- what gets built
      +-- docs/sourcing/PROJECT-BOM.*  generated shopping list
```

New wiring facts go into the master row **first**; `channels.csv` (ECU channel settings), the IO table, the drawings and
the BOM follow. Device pin, pin name and whether that device gets a shield go into
`docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` (one shield flag per device, never per pin or wire). Which ECU pin a
device wire lands on is owned by the ECU; ECU pins never move. If anything disagrees with the master on a pin, the other
thing is wrong - never the reverse. No script writes the master or `channels.csv`.
`python tools/check_all.py` enforces the whole chain and must pass before every commit.

### ECU pins: check the Quick Start Guide and the plug-in guides (R212)

A wire on an ECU pin (plugs A / B / C) is also checked against the Link G4X Quick Start Guide and the G4X plug-in
(wire-in) guides (the plug-in guide wins for special circuits and pin modes): pin function and mode, what the pin may
connect to, current limits, wire gauge. `docs/harness/tools/check_wiring.py` fails on any far end the pin's class does
not allow (R212), any ground that breaks the ground classes (R213, R216), any relay driven the wrong way (R219); known
violations waiting for the wiring fix are listed in its `PENDING`.

### Every wiring surface that must agree

| Surface | Role |
|---|---|
| `docs/harness/MASTER-wirelist.csv` | The ONE wiring SoT (R221) |
| `sot/channels.csv` | ECU channel settings; pins checked against the master |
| `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` | Device pin, pin name, shield flag per device |
| `XTREMEX-IO-TABLE.html` | Visual face of `channels.csv`, with a generated pin map |
| `docs/harness/drawings/` | Generated drawing sets (re-run `tools/build_drawings.py`, never edit the PDF) |
| `docs/harness/routes/` | Dan's approved routes; a drawing's path follows its route |
| `cad/fusebox/` | The fuse-box design (slot map `rev7/wiring_plan.json`, R204) |
| `docs/sourcing/PROJECT-BOM.csv` | Generated - re-run `build_project_bom.py` |
| `docs/harness/redesign/DECISIONS.md` | The binding rules (B1-B30) |
| `docs/SHIELD-RULES.md` | Shield rules, enforced by `check_wiring.py` S1-S3 |
| `docs/sourcing/te-on-hand-bom.csv` | Parts already owned - check before speccing anything new |

Generated files are never hand-edited - re-run their script.

### No factory engine-bay wire is reused

Rule **B9** in `DECISIONS.md` (old R11). Applied here: an OEM end on an engine-bay harness (`EngineRoom-C`, `AB-engine`,
`HeavyDC`) is a new-wire run to the device's own plug, never a splice into a factory lead.

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

## Rule 3 — the ECU harness: one harness, cabin side and engine side

**Daniel, 2026-10-19 (DECISIONS R220): loom A and loom B are one harness**, named `AB` - "they both come from the same
bulkhead". It replaces the 2026-09-28 connector-letter split.

- **Two sides in the master:** `AB-cabin` (ECU plugs A, B and C to the cabin half of the DRB102 bulkhead, plus every cabin
  branch) and `AB-engine` (the engine half of the bulkhead to every engine device the ECU drives or reads, the throttle body
  included). The letters A / B / C are the ECU's own plug names and stay on the pins; the ECU pin assignments never move.
- **One bulkhead connector per side:** `DRB102-CABIN` and `DRB102-ENGINE` (TE drawing DRB12-102PXE-L018), cavities assigned
  by device (R208); the map is generated, `docs/harness/drawings/DRB102-bulkhead-map.png`.
- **The ECU splice point:** every cabin power, ground and rail splice sits at one place by the ECU plugs. +5 V (A32) is two
  bussed DT plugs `BUS-5V` (12-way) and `BUS-5V-2` (8-way, linked); Gnd Out A24 and B22 are their own 12-way bussed DT plugs
  `BUS-GNDOUT-A` / `BUS-GNDOUT-B` (no A24-B22 tie); +8 V, switched 12 V, the ECU A5 feed and the ECU power ground are
  soldered splices there (R169 parts: `DT06-12SA` / `DT04-12PA-P021`, `DT06-08SA` / `DT04-08PA-P021`, 13 A per pin). The ECU
  power ground splice joins A25, A34, B25, B34 only and runs one wire to the POWER box battery-negative bar (R216).
- **Splice sizing:** rule **R36** (combined gauge; not for drains, R30). **Connector substitution:** rule **R8**.
- A wire belongs to the one harness that carries it (`harness` column); `passes_through` names any harness it runs
  through. Mating halves (DRB102, the inline `IX-` pairs) are checked cavity for cavity by `check_wiring.py` M1.
- Every other harness keeps its own name: `CabinPower`, `HeavyDC`, `EngineRoom-C`, `CAN`, `CSB3`, `ClusterLED`,
  `AntiTheft`, `RearFuel`, `RearLights`, `WheelSpeed-Front` / `-Rear`.

---

## Scope note

These rules cross repository boundaries. The cluster repo is checked out alongside this one
at `C:\projects\active\center-cluster-esp32-p4`, so references such as `main/canbus.c`
resolve there, not here. A CAN change in this repo that affects the cluster is not complete
until the cluster side is checked, even though it lives in a different repository.

The only center-cluster portion in this repo is the CAN node, plus power and
ground to the cluster. Interior cluster wiring lives only in the center
cluster repo. Do not add interior cluster circuits here.
