# Reconciliation rules — binding on every agent

Agent-agnostic. Claude Code, Cursor, Codex, or any other tool: these apply. The
per-agent rule files (`.cursor/rules/`, `.claude/rules/`, `AGENTS.md`) point here for the
**procedure**. The rule statements themselves (what Daniel decided, dated, R1-R88) are
owned by `docs/harness/redesign/DECISIONS.md` "Binding rules from Daniel"; this file says
how to apply them and which surfaces must agree. Where the two disagree, `DECISIONS.md` wins.

Three rules. Rules 1 and 2 exist because this project has repeatedly drifted: a change
landed in one document and its siblings silently disagreed for weeks. Rule 3 is how the
ECU looms are divided, and this file owns its wording.

---

## Rule 1 — Wiring: reconcile ALL wiring documents, not just the one you touched

**Trigger:** any change to any wiring document, diagram, harness file, pinout, or BOM.

**Requirement:** before the change is final, check it against the source-of-truth chain
**and** against every other wiring surface listed below — including the ones you did not
edit. They must all agree. A change that leaves two documents disagreeing is not done.

### Source-of-truth chain

```
sot/channels.csv             ECU pin and channel SoT
      |
      +-- docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md
      |     device pin, pin name, whether that device gets a shield
      +-- XTREMEX-IO-TABLE.html        visual face; sync_io_table.py --check gates it
      +-- docs/harness/rebuild/*.harness   the physical looms  <- what gets built
              |
              +-- harness.design app copy   mirror - never edit as source
```

New ECU pin facts go into `sot/channels.csv` **first** (Daniel, 2026-09-25), then the IO
table and the looms follow. Device pin, pin name, and whether that device gets a
shield go into `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`. One shield flag
per device or sensor, not per connector pin and not per wire. Which ECU pin a
device wire lands on is owned by the ECU. If anything disagrees with the CSV on
an ECU pin, the other thing is wrong and gets corrected - never the reverse.
`python docs/harness/check_all.py` enforces the whole chain and must pass before
every commit.

### Every wiring surface that must agree

| Surface | Role |
|---|---|
| `sot/channels.csv` | ECU pin/channel SoT |
| `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` | Device pin, pin name, whether that device gets a shield (one flag per device, never per pin or wire) |
| `XTREMEX-IO-TABLE.html` | Visual face of the ECU SoT, with a generated pin map |
| `docs/harness/rebuild/ST185-A-cabin.harness` | ECU connector A to cabin bulkhead A: the A-pin relay coil wires (broken off to the box), the BRZ APS pedal connector (Rule 3 crossover c), front wheel-speed spur, the +5V / Gnd Out splices (Rule 3) |
| `docs/harness/rebuild/ST185-B-cabin.harness` | ECU connector B to cabin bulkhead B: the B-pin relay coil wires (broken off to the box), fuel level branch, rear wheel-speed spur, the APS B33 leg broken off from A-cabin (Rule 3 crossover c) |
| `docs/harness/rebuild/ST185-CabinPower.harness` | Glove-box POWER + LOGIC fuse boxes (DECISIONS R75, CAD rev 5) with the ECU-switched relays seated in them (all but `k_fp`), battery feed (non-ECU) |
| `docs/harness/rebuild/ST185-CSB3.harness` | ECUMaster CSB3 plug and switch inputs (non-ECU) |
| `docs/harness/rebuild/ST185-A-engine.harness` | Bulkhead A engine half to every A-letter engine device (Rule 3) |
| `docs/harness/rebuild/ST185-B-engine.harness` | Bulkhead B engine half to every B-letter engine device, ETB motor (Rule 3) |
| `docs/harness/rebuild/ST185-CAN.harness` | CAN backbone - the only drawing with CAN H/L |
| `docs/harness/rebuild/ST185-EngineRoom-C.harness` | Loom C engine room, no bulkhead |
| `docs/harness/rebuild/ST185-WheelSpeed-Front.harness` / `-Rear.harness` | Wheel-speed Y harnesses to VRC endpoints and `IX_WS_FRONT` / `IX_WS_REAR` |
| `docs/harness/rebuild/ST185-RearFuel.harness` | Fuel level sender behind `IX_FUEL_LVL`; fuel pump + ground, fed from `k_fp` (HeavyDC battery relay block) |
| `docs/harness/interfaces.json` | Ownership registry: interfaces, endpoints, flying leads, references |
| `docs/harness/rebuild/ST185-ClusterLED.harness` | Cluster warning LEDs |
| `docs/harness/rebuild/ST185-AntiTheft.harness` | Anti-theft |
| `docs/harness/rebuild/ST185-RearLights.harness` | Rear lights: J/B No.1 / S9 feeds to the rear lamps, reverse from `k_rev` |
| `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` | Cabin landing table for every ex-J/B2 / R/B load (§5.4), fuse-box slot map (§8.1) |
| `docs/harness/HARNESS-BUILD-LIST.csv` | Generated - re-run `buildlist.py` |
| `docs/harness/NEED-TO-BUY.md` | Generated - re-run `buylist.py` |
| `docs/harness/redesign/DECISIONS.md` | The binding rules (R1-R88) and the dated decisions |
| `docs/SHIELD-RULES.md` | Shield rules, enforced by the audits |
| `docs/sourcing/te-on-hand-bom.csv` | Parts already owned - check before speccing anything new |

The four ECU loom files follow the ECU connector letter (Rule 3). Per **bulkhead**, every
cavity on the bulkhead A cabin half mates the same cavity on the bulkhead A engine half,
same for B. `audit_mating.py`, `audit_pin_names.py` and `validate_bulkhead_letter.py`
check that.

The frozen pre-split baseline and `verify_rebuild.py` were retired on 2026-09-27;
`verify_connectivity.py` replaced them. Dated audit notes and one-shot fix scripts
are not authoritative.

Generated files are never hand-edited — re-run their script.

### No factory engine-bay wire is reused

Rule **R11** in `DECISIONS.md` (Daniel, 2026-10-04 / 2026-10-12). Applied here: an
`oem_flying_lead` on an engine-bay harness (`EngineRoom-C`, `A-engine`, `B-engine`,
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

## Rule 3 — ECU looms follow the ECU connector letter

**Daniel, 2026-09-28.** Binding; it overrides the handoff's "Rule 10 A = signal / B =
power", redesign decision D3 and Phase 7 of `docs/harness/redesign/`, and the merged
`ST185-ECU-Cabin` drawing (retired).

- **ECU connector A → cabin firewall A → engine firewall A → engine bay.** Connector B the
  same, on bulkhead B.
- **Exactly four ECU harness files:** `ST185-A-cabin`, `ST185-B-cabin`, `ST185-A-engine`,
  `ST185-B-engine`. A wire's letter is the ECU pin's `conn` column in `sot/channels.csv`.
- **Non-ECU wires** (fused 12V, relay outputs, grounds) follow the bulkhead of the ECU
  signal of the device they serve.
- **The only crossovers:**
  - **(a)** +5V sensor supply (A32) splices in the **cabin** at ECU A and feeds both
    letters (ECU B has no +5V). Sensor ground is **not** shared across letters: loom A's
    sensors return to Gnd Out A24, loom B's to its own Gnd Out B22, with no A24-B22 tie in
    the harness (Daniel, 2026-09-28: never splice A-owned sensor ground into the B looms
    while ECU B has its own).
    **Tapered distribution (Daniel, 2026-09-28):** the ECU pin leads (A32, A24, B22) are
    18 AWG (the largest the Superseal 1.0 contact takes); 18 AWG trunks run from the ECU
    splices to a splice just before cabin bulkhead A (`sp_5v_bha` / `sp_gnd_bha`) and to the
    loom B splices `sp_5v_b` (+5V trunk from A) and `sp_gndout_b` (B22 lead) with
    `sp_gnd_bhb` before bulkhead B; each rail then crosses on several 20 AWG bulkhead
    pins (A: c2, c39, c40 +5V; c3, c41-c44 Gnd. B: c17 knock return, c19, c21 Gnd) that run
    straight to one device or to a small engine-side branch splice. Every splice is a
    generic soldered splice point. The B-engine sensors' +5V crosses on bulkhead A
    c45-c47 and runs as a short A-engine spur to the DT 6-way inline pair `IX_B_RAIL`
    (DT06-6S on A-engine, DT04-6P on B-engine, c4-c6 spare), one +5V pin per pressure
    sensor (Daniel, 2026-09-28). Bulkhead cavities and spares follow the real DRB102
    cavity map, `docs/harness/DRB102-CAVITY-MAP.md` (from TE's drawing, 2026-10-11; gate
    `audit_mating.py` M8): A has 7 size-16 spares plus 3 shield-drain cavities
    (c6, c10, c11); B has 13 size-16, 12 size-12, 4 size-8 and 2 size-4 spares plus 3
    shield-drain cavities (c22-c24). The old HDP20-era "bulkhead B has no size-16/20
    spare" limit is gone; every shield drain gets its own cavity.
  - **(b)** ETB: relay trigger on A20, H-bridge supply on B5 (by ECU pin design).
  - **(c)** APS pedal: channel 1 on A14, channel 2 on B33 (by ECU pin design). All pedal
    wiring stays in the cabin: the BRZ e-throttle pedal connector itself is drawn on
    `ST185-A-cabin` (folded in from the retired `ST185-APS-Pedal` 2026-10-11, "pedal is
    one cable in A-cabin") - 5 of 6 pins wire straight from there; only the B33 leg
    (conductor `w_aps_vpa2`) breaks off to `ST185-B-cabin`, the one allow-listed A-file
    wire reaching a B-letter device cavity (`docs/harness/validate_bulkhead_letter.py`
    `ALLOW["c"]`). The throttle **body** (A20 relay trigger, B5 supply, B18/B26 motor,
    A22/A33 sensors) is engine-bay wiring.
  - The injector rail (LOGIC INJ 15 A) and COP rail (LOGIC COP 15 A) are **not** a crossover:
    non-ECU power follows its device's ECU signal letter, so they cross on the A side, on
    bulkhead A c48 / c49 of the shared DRB102 (`docs/harness/DRB102-CAVITY-MAP.md`). The
    earlier `IX_RAIL_A` DTP pass-through is retired (2026-09-29). Crossover (d) is retired
    (Daniel, 2026-09-28; `docs/harness/redesign/DECISIONS.md` Q-RAIL).
- **Splice sizing:** rule **R36** (combined gauge, Wire Barn calculator; not for drains, R30).
  Gate: `audit_cavity_parts.py` K3.
- **Connector substitution:** rule **R8** (complete matching set, datasheet part numbers). The
  pair is registered as an inline interface in `docs/harness/interfaces.json` and counted on
  the buy list.
- **ETB body (engine bay):** the B18 / B26 motor wires leave `ST185-B-engine` as a short spur
  right after bulkhead B, drawn broken off with a note; `ST185-A-engine` shows them broken
  off coming in from B-engine and takes them into the A trunk, under the sheathing, right
  after bulkhead A, to the throttle body drawn there.
- **No harness is drawn inside another** (all power and ECU harnesses). A wire that runs
  between two harness files is drawn **broken off in both**, each section ending at a noted
  terminal that names the other file; a device is drawn once. Where that will not resolve,
  put a connector pair where the wire leaves one harness and enters the other, with a note
  in both files naming the other. Non-ECU wires that follow a device's bulkhead obey the
  same rule. No cross-reference dummies. The pairs are registered in
  `docs/harness/interfaces.json` "breaks"; `validate_bulkhead_letter.py` L6 / L7 enforce
  them.
- The ECUMaster CSB3 plug and its switch inputs are their own non-ECU harness,
  `ST185-CSB3` (keeps `ST185-A-cabin` under the harness.design 100-connection limit).
- The glove-box POWER + LOGIC fuse boxes (DECISIONS R75, CAD rev 5) and the battery feed ring
  are the non-ECU harness `ST185-CabinPower` (Daniel, 2026-09-28, same reason). The fuel pump
  relay `k_fp` sits in the battery relay block in the trunk, drawn in `ST185-HeavyDC`; the pump
  run is `ST185-RearFuel`. The boxes live in that file only; every other file reaches it through broken-off pairs. The ECU-switched
  relays sit in the boxes and are drawn there; their ECU coil (85) wires stay on the ECU loom of
  the pin's letter (`ST185-A-cabin` / `ST185-B-cabin`) and break off to the box (2026-10-11, OPEN-ITEMS row 45).
- Every other loom stays as it is: `EngineRoom-C`, `CAN`, `ClusterLED`, `AntiTheft`,
  `WheelSpeed-Front` / `-Rear`, `RearFuel`, `HeavyDC`, `RearLights` (added 2026-10-13). `ACAmp-Spur` and `APS-Pedal` were
  retired 2026-10-11 - their non-ECU content folded into `A-cabin` (and, for the A/C
  device-side leads, `EngineRoom-C`); crossover (c) above covers what crosses letters.

**Enforced by** `docs/harness/validate_bulkhead_letter.py`, a hard gate in `check_all.py`.
Its allow-list is (a)-(c) and nothing else.

---

## Scope note

These rules cross repository boundaries. The cluster repo is checked out alongside this one
at `C:\projects\active\center-cluster-esp32-p4`, so references such as `main/canbus.c`
resolve there, not here. A CAN change in this repo that affects the cluster is not complete
until the cluster side is checked, even though it lives in a different repository.

The only center-cluster portion in this repo is the CAN node, plus power and
ground to the cluster. Interior cluster wiring lives only in the center
cluster repo. Do not add interior cluster circuits here.
