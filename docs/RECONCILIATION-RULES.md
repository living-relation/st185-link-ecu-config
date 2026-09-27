# Reconciliation rules — binding on every agent

Agent-agnostic. Claude Code, Cursor, Codex, or any other tool: these apply. The
per-agent rule files (`.cursor/rules/`, `.claude/rules/`, `AGENTS.md`) all point here,
and this file is the wording they defer to.

Two rules. Both exist because this project has repeatedly drifted: a change landed in one
document and its siblings silently disagreed for weeks.

---

## Rule 1 — Wiring: reconcile ALL wiring documents, not just the one you touched

**Trigger:** any change to any wiring document, diagram, harness file, pinout, or BOM.

**Requirement:** before the change is final, check it against the source-of-truth chain
**and** against every other wiring surface listed below — including the ones you did not
edit. They must all agree. A change that leaves two documents disagreeing is not done.

### Source-of-truth chain

```
sot/channels.csv             every pin and channel    <- SoT, nothing outranks it
      |
      +-- XTREMEX-IO-TABLE.html        visual face; sync_io_table.py --check gates it
      +-- docs/harness/rebuild/*.harness   the physical looms  <- what gets built
              |
              +-- docs/harness/min/*.harness   upload copies (make_min.py)
                      |
                      +-- harness.design app copy   mirror - never edit as source
```

New pin facts go into `sot/channels.csv` **first** (Daniel, 2026-09-25), then the IO
table and the looms follow. If anything disagrees with the CSV, the other thing is wrong
and gets corrected - never the reverse. `python docs/harness/check_all.py` enforces the
whole chain and must pass before every commit.

### Every wiring surface that must agree

| Surface | Role |
|---|---|
| `sot/channels.csv` | Pin/channel SoT |
| `XTREMEX-IO-TABLE.html` | Visual face of the SoT, with a generated pin map |
| `docs/harness/rebuild/ST185-A-ECU.harness` | Cabin side, signal circuits from both ECU connectors to the bulkhead A and B cabin halves |
| `docs/harness/rebuild/ST185-A-engine.harness` | Engine side of those signal circuits |
| `docs/harness/rebuild/ST185-B-ECU.harness` | Cabin side, power: ECU power pins, relays, cabin fuse block |
| `docs/harness/rebuild/ST185-B-engine.harness` | Engine side of those power circuits |
| `docs/harness/rebuild/ST185-CAN.harness` | CAN backbone - the only drawing with CAN H/L |
| `docs/harness/rebuild/ST185-EngineRoom-C.harness` | Loom C engine room, no bulkhead |
| `docs/harness/rebuild/ST185-WheelSpeed.harness` | Wheel speed drops + VR conditioners (front = loom C fender sub-loom) |
| `docs/harness/rebuild/ST185-ClusterLED.harness` | Cluster warning LEDs |
| `docs/harness/rebuild/ST185-AntiTheft.harness` | Anti-theft |
| `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` | Kick-panel / J/B2 splice table |
| `docs/harness/HARNESS-BUILD-LIST.csv` | Generated - re-run `buildlist.py` |
| `docs/harness/NEED-TO-BUY.md` | Generated - re-run `buylist.py` |
| `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` | Build rules (section 6) |
| `docs/SHIELD-RULES.md` | Shield rules, enforced by the audits |
| `docs/sourcing/te-on-hand-bom.csv` | Parts already owned - check before speccing anything new |

The file names do not follow the bulkhead letter - a file can carry both bulkheads.
What must hold is per **bulkhead**: every cavity on the bulkhead A cabin half mates the
same cavity on the bulkhead A engine half, same for B, and a circuit crosses on the
bulkhead of its ECU pin's loom. `audit_mating.py` and `audit_pin_names.py` check that.

**Every file is exactly one loom, and a connector belonging to a different loom never
appears in it - full stop, regardless of how it would be related to the rest of the
file.** A bulkhead's two halves genuinely **mate**: the connector faces are a compatible
plug/socket pair per the manufacturer spec, and that is a real, correct fact about the
car. The mistake is not the word "mate" and not the fact that they mate - it is letting
that fact pull both halves, or any two connectors from different looms, into one file:

- **One loom, one file, no exceptions.** `bh_a_fw` (ECU harness A, cabin) lives only in
  `ST185-A-ECU.harness`; `bh_a_eng` (engine harness A) lives only in
  `ST185-A-engine.harness`. Same for `bh_b_fw` / `bh_b_eng` and for `ecu_a` / `ecu_b`
  themselves - `ST185-A-ECU` carries `ecu_a` and never `ecu_b`, `ST185-B-ECU` the
  reverse. If two connectors belong to different looms, they never sit in the same file -
  not wired together, not related by a `mates` entry, not one of them present as an
  unrelated duplicate. Needing them in the same place to relate them is the sign to keep
  them apart, not the justification for combining the files.
- **No wire, no cable core, and no `mates` entry ever joins a `bh_*_fw` cavity to its
  matching `bh_*_eng` cavity** - not because a mate would be the wrong word for what
  happens at a firewall (it is exactly the right word), but because the two halves belong
  to two different looms, and two different looms' connectors are never in one file
  together for any reason. A wire that reaches a bulkhead cavity from the ECU side stops
  there; a wire that reaches the same-numbered cavity from the engine side starts there.
  The pairing is expressed only by both halves sharing the same cavity **number** (`c7`
  cabin = `c7` engine) and the same real connector part pair - never by anything living in
  the graph. `audit_bulkhead_pairs.py` (both sides wired or neither) and `audit_mating.py`
  (continuity traced through the pairing back to the SoT) check the pairing by comparing
  the separate files; they work precisely because there is nothing to follow inside one.
- **A `mates` entry is for two connectors that are genuinely part of the same loom** (a
  terminal plugged into a connector within one harness assembly) - never for two
  connectors from different looms, and never as a reason to put them in one document.
- If a **third** drawing needs to reference a cavity that physically lives on another
  loom's connector (loom C's MRS pump splicing off bulkhead A's engine-side cavity 36 is
  the working example), it draws a minimal `dm_bh_<bulkhead>_<cavity>` cross-reference
  connector - no `partId`, no cavities beyond the one being referenced,
  `excludeFromBom: true` in harness.design - and lands its wire on that. It never gets a
  full duplicate of the real connector, real part number or not, and never a live edge to
  the connector in the other file/document.

`docs/harness/legacy-prebuild/` is the frozen baseline `verify_rebuild.py` diffs against.
Read it, never edit it. Retired diagrams, dated audit notes and one-shot fix scripts live in
`archive/2026-09-25-cleanup/` and are not authoritative.

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

## Scope note

These rules cross repository boundaries. The cluster repo is checked out alongside this one
at `C:\projects\shipping\center-cluster-esp32-p4`, so references such as `main/canbus.c`
resolve there, not here. A CAN change in this repo that affects the cluster is not complete
until the cluster side is checked, even though it lives in a different repository.
