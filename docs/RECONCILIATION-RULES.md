# Reconciliation rules — binding on every agent

Agent-agnostic. Claude Code, Cursor, Codex, or any other tool: these apply. The
per-agent rule files (`.cursor/rules/`, `.claude/rules/`, `AGENTS.md`) all point here,
and this file is the wording they defer to.

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
              +-- docs/harness/min/*.harness   upload copies (make_min.py)
                      |
                      +-- harness.design app copy   mirror - never edit as source
```

New ECU pin facts go into `sot/channels.csv` **first** (Daniel, 2026-09-25), then the IO
table and the looms follow. Device pin, pin name, and whether that device gets a
shield go into `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`. Which ECU pin a
device wire lands on is owned by the ECU. If anything disagrees with the CSV on
an ECU pin, the other thing is wrong and gets corrected - never the reverse.
`python docs/harness/check_all.py` enforces the whole chain and must pass before
every commit.

### Every wiring surface that must agree

| Surface | Role |
|---|---|
| `sot/channels.csv` | ECU pin/channel SoT |
| `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md` | Device pin, pin name, whether that device gets a shield |
| `XTREMEX-IO-TABLE.html` | Visual face of the ECU SoT, with a generated pin map |
| `docs/harness/rebuild/ST185-A-cabin.harness` | ECU connector A to cabin bulkhead A: A-triggered relays, APS, front wheel-speed spur, the +5V / Gnd Out splices (Rule 3) |
| `docs/harness/rebuild/ST185-B-cabin.harness` | ECU connector B to cabin bulkhead B: condenser fan relay, fuel level branch, rear wheel-speed spur (Rule 3) |
| `docs/harness/rebuild/ST185-APS-Pedal.harness` | APS pedal harness: A/B pedal wires broken off the cabin looms, female/male DT 6-way pair, run to the pedal (Rule 3 crossover c) |
| `docs/harness/rebuild/ST185-CabinPower.harness` | Cabin fuse block, HCFB, battery feed, fuel pump run (non-ECU) |
| `docs/harness/rebuild/ST185-CSB3.harness` | ECUMaster CSB3 plug and switch inputs (non-ECU) |
| `docs/harness/rebuild/ST185-A-engine.harness` | Bulkhead A engine half to every A-letter engine device (Rule 3) |
| `docs/harness/rebuild/ST185-B-engine.harness` | Bulkhead B engine half to every B-letter engine device, ETB motor (Rule 3) |
| `docs/harness/rebuild/ST185-CAN.harness` | CAN backbone - the only drawing with CAN H/L |
| `docs/harness/rebuild/ST185-EngineRoom-C.harness` | Loom C engine room, no bulkhead |
| `docs/harness/rebuild/ST185-WheelSpeed-Front.harness` / `-Rear.harness` | Wheel-speed Y harnesses to VRC endpoints and `IX_WS_FRONT` / `IX_WS_REAR` |
| `docs/harness/rebuild/ST185-RearFuel.harness` | Fuel level sender behind `IX_FUEL_LVL` |
| `docs/harness/rebuild/ST185-ACAmp-Spur.harness` | A/C amplifier spur behind `IX_AC_CTS` |
| `docs/harness/interfaces.json` | Ownership registry: interfaces, endpoints, flying leads, references |
| `docs/harness/rebuild/ST185-ClusterLED.harness` | Cluster warning LEDs |
| `docs/harness/rebuild/ST185-AntiTheft.harness` | Anti-theft |
| `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` | Kick-panel / J/B2 splice table |
| `docs/harness/HARNESS-BUILD-LIST.csv` | Generated - re-run `buildlist.py` |
| `docs/harness/NEED-TO-BUY.md` | Generated - re-run `buylist.py` |
| `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` | Build rules (section 6) |
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

---

## Rule 2 — CAN: any change on any device reconciles across all devices

**Trigger:** any change to CAN configuration on **any** device, in **any** repo.

**Requirement:** reconcile and verify against every other CAN participant before the change
is final. All of them, every time — not just the pair you happened to be working on.

### The participants

| Device | Where its config lives |
|---|---|
| **Link G4X XtremeX ECU** | `link_g4x_can_setup.json`, `link_g4x_can_setup.lcs`, `CANBUS-LINK-G4X-CONFIG.md` |
| **Center cluster (ESP32-P4)** | `center-cluster-esp32-p4` repo — `main/canbus.c`, `main/protocols/link_g4x.json` |
| **RealDash** | `link_g4x_realdash.xml`, `st185_dash.rd`, `REALDASH-LAYOUT.md`, `rd-build/` |
| **ECUMaster CAN Switchboard (CSB3)** | `ECUMASTER_SWITCHBOARD_SETUP.md` |
| **Link CAN-Lambda** | On the same bus — see bus facts below |

Shared contract documents that must also stay in step: `CAN-BUS-ID-ALLOCATION-TABLE.md`,
`CAN-BUS-MASTER-DESIGN.md`, `CAN-CONFIG-STATUS.md`, `CANBUS-ENCODE-DECODE-REFERENCE.html`,
`BENCH-TEST.md`, `bench/frames.py`.

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
    sensor (Daniel, 2026-09-28). Spare bulkhead cavities: A c1 (size 16), c6, c10-c12,
    c27, c28, c30-c32 (size 20); B c1, c2 (size 12). Bulkhead B has no size-16 or size-20
    spare for a screen drain (Daniel, 2026-09-28: accepted).
  - **(b)** ETB: relay trigger on A20, H-bridge supply on B5 (by ECU pin design).
  - **(c)** APS pedal: channel 1 on A14, channel 2 on B33 (by ECU pin design). All pedal
    wiring stays in the cabin: the A pedal wires break off `ST185-A-cabin` and the B33
    wire breaks off `ST185-B-cabin`, both at the female DT 6-way of `IX_APS`, and
    `ST185-APS-Pedal` runs from the male half to the pedal. The throttle **body** (A20
    relay trigger, B5 supply, B18/B26 motor, A22/A33 sensors) is engine-bay wiring.
  - The injector rail (F11 15 A) and COP rail (F10 20 A) are **not** a crossover: non-ECU
    power follows its device's ECU signal letter, so they cross on the A side through
    `IX_RAIL_A`, a Deutsch DTP 4-way flange pass-through beside bulkhead A (`ST185-A-cabin`
    receptacle, `ST185-A-engine` plug). Crossover (d) is retired (Daniel, 2026-09-28;
    `docs/harness/redesign/DECISIONS.md` Q-RAIL).
- **Splice sizing (Daniel, 2026-09-28, standing):** a splice is sized by the **combined** gauge
  of the wires it joins, from the Wire Barn Combined Wire Gauge Calculator
  (https://www.wirebarn.com/Combined-Wire-Gauge-Calculator_ep_42.html). The splice part's range
  must cover the combined gauge, not each wire (4 x 20 AWG = 1 x 14 AWG, fits a 14-10 splice).
  harness.design flags splices whose individual wires are below the part's minimum gauge
  ("wires are too thin"); that per-wire warning is a known false alarm and is not chased.
- **Connector substitution (Daniel, 2026-09-28, standing):** if bulkhead A or B runs out of
  pins or needs higher-capacity contacts, a different connector may replace it or a second
  one may be added beside it - but only with a **complete, compatible matching set for both
  sides**: housings, inserts, contacts for each wire gauge, seals and cavity plugs,
  wedgelocks, mounting gasket or backshell where the family has one. Every part number comes
  from the maker's datasheet or catalog; nothing is guessed. The pair is registered as an
  inline interface in `docs/harness/interfaces.json` and counted on the buy list.
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
- The cabin fuse block, HCFB, battery feed ring and fuel pump run are the non-ECU harness
  `ST185-CabinPower` (Daniel, 2026-09-28, same reason). The relays stay on `ST185-A-cabin`:
  their ECU-A trigger gives them letter A.
- Every other loom stays as it is: `EngineRoom-C`, `CAN`, `ClusterLED`, `AntiTheft`,
  `WheelSpeed-Front` / `-Rear`, `RearFuel`, `ACAmp-Spur`.

**Enforced by** `docs/harness/validate_bulkhead_letter.py`, a hard gate in `check_all.py`.
Its allow-list is (a)-(c) and nothing else.

---

## Scope note

These rules cross repository boundaries. The cluster repo is checked out alongside this one
at `C:\projects\shipping\center-cluster-esp32-p4`, so references such as `main/canbus.c`
resolve there, not here. A CAN change in this repo that affects the cluster is not complete
until the cluster side is checked, even though it lives in a different repository.
