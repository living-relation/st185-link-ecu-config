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
XTREMEX-IO-TABLE.html        ECU pins + channels      ← SoT, nothing outranks it
      ↓
SCHEMATIC-WIRING.html        print face (derived)
apps/harness-schematic/      interactive face (derived)
      ↓
docs/harness/*.harness       Power / Signal / CAN / EngineRoom-C  ← physical SoT
      ↓
harness.design app copy      mirror — never edit as source
```

New pin facts go into `XTREMEX-IO-TABLE.html` **first**, then propagate outward. If a
downstream face disagrees with the table, the face is wrong and gets corrected — never the
reverse.

### Every wiring surface that must agree

| Surface | Role |
|---|---|
| `XTREMEX-IO-TABLE.html` | Pin/channel SoT |
| `SCHEMATIC-WIRING.html` | Print face |
| `apps/harness-schematic/index.html` | Interactive face |
| `docs/harness/ST185-Signal.harness` | Signal loom |
| `docs/harness/ST185-Power.harness` | Power loom |
| `docs/harness/ST185-CAN.harness` | CAN loom |
| `docs/harness/ST185-EngineRoom-C.harness` | Partial engine-room add-on + OEM J/B injection |
| `docs/electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` | Kick-panel / J/B2 splice table |
| `docs/harness/HARNESS-BUILD-LIST.csv` | Generated — re-run `buildlist.py` |
| `docs/harness/NEED-TO-BUY.md` | Generated — re-run `buylist.py` |
| `docs/HARNESS-CONSOLIDATION-AND-LAYOUT-PLAN.md` | Build rules and doc roles |
| `WIRING.md` | Cluster GPIO + CAN physical topology |
| `SENSORS_AND_COMPONENTS_MASTER.csv` | Device names, part numbers, locations |

Dated `VERIFY` / `AUDIT` / `FACES` / `BOARD-VERIFY` notes in `docs/` are **frozen records**.
Read them, never update them, never treat them as living pin maps.

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
