# Harness files - which one is current

Written 2026-09-22, rewritten 2026-09-27 for the harness redesign. Read this before
opening any loom.

**The wiring source of truth is `sot/channels.csv`** (every ECU pin and channel).
The looms below are the physical build and must agree with it; `check_all.py`
enforces that. **Every rule for drawing them is in `redesign/DECISIONS.md` "Binding rules
from Daniel" (R1-R67)** - this file is the file map and the workflow, and restates no rule.

## The short answer

**`rebuild/` holds the current drawings - edit the looms there. Everything else here is a copy,
a build product, or history.** The drawings are **not a source of truth** (Daniel,
2026-10-04): they follow `sot/channels.csv`, and no truth document is generated from them.

| Folder / file | What it is | Edit it? |
|---|---|---|
| **`rebuild/`** | The 15 current harnesses. Human-readable JSON, what git diffs, what matches harness.design | **Yes - edit the drawings here** (not a source of truth) |
| **`routes/`** | Dan's approved route drawing for each harness (one HTML per route, current version only; git history keeps the revisions). A drawing's path must match its route. Lint: `check_route_drawings.py` (SOFT gate) | Only from Dan's markup (`st185-apply-route-markup`) |
| **`interfaces.json`** | Who owns what: physical harness per file, inline interface pairs, VRC endpoints, OEM flying leads with EWD locators, broken-off pairs. harness.design rejects unknown keys, so this cannot live in the drawings | **Yes - with the drawings** |
| `rebuild/ST185.harnesslib` | The harness.design local part library (same JSON as a `.harness`, part arrays only), kept next to the drawings so the desktop app links it from the folder it opens. Every part the drawings use, equal to the drawing; update it in the same PR as any part change | **Yes - with the drawings** (gate `check_harnesslib.py`) |
| `redesign/` | Decision record, implementation plan, interface convention | Decisions only by agreement |

## Open in the desktop app

Dan edits the drawings in the harness.design **desktop app**, which opens the files and reloads live
(https://docs.harness.design/feature/desktop). No upload step; cloud copies are for sharing only.

- **Open the files** in `docs/harness/rebuild/` (File > Open..., or double-click a `.harness`). The app opens one file at a time, watches it and reloads saved changes at once; `min/` no longer exists.
- **Link the part library once:** Preferences > Part Libraries > Link existing > `rebuild/ST185.harnesslib`. The library wins on part data; it is committed with the drawings.
- **Flow:** edit in the app (it saves the file itself), then run `python docs/harness/check_all.py`, commit the drawing and any `.harnesslib` change together.
- **Agents pause while Dan edits.** The version saved to disk wins: if the app has unsaved edits when an agent saves, the app's edits are discarded. An agent never rewrites a file Dan has open with unsaved changes. The gates read the JSON, not its whitespace, so the app's own formatting never fails CI.
- Free plan: 100 connections per harness also applies to local files. The app rejects unknown keys, so repo-only data lives in `interfaces.json`, never in a `.harness`.
- Agents: use the global skill `harness-design` (`C:/Users/danie/.claude/skills/harness-design/SKILL.md`).

## The 15 harnesses

Each file is one physical harness that gets built. Shared nets may cross a boundary; a
physical section of copper, a connector or a BOM line has one owner.

| File | Harness | Scope |
|---|---|---|
| `ST185-A-cabin.harness` | ECU connector A, cabin | ECU-A, cabin half of bulkhead A, the A-pin relay coil wires (relays are in the box, CabinPower), the BRZ APS pedal connector (folded in 2026-10-11, B33 leg breaks off to B-cabin), the A/C amplifier's cabin-side flying leads (folded in from ST185-ACAmp-Spur 2026-10-11: TW/return, kill, clutch and pressure-switch taps at the amplifier - the A4/A5 device-side ends are on EngineRoom-C), front wheel-speed spur, the +5V / Gnd Out / +8V / switched-12V splices |
| `ST185-B-cabin.harness` | ECU connector B, cabin | ECU-B, cabin half of bulkhead B, the B-pin relay coil wires (k_fan2 / k_eps_en / k_acc are in the box, CabinPower), fuel level branch, rear wheel-speed spur, the front spur's FR core, the B legs of +5V / Gnd Out |
| `ST185-CabinPower.harness` | Cabin power (non-ECU) | the glove-box fuse box (Option B: Bussmann LMI in two stacks `lmi_a_*` / `lmi_b_*` (L1-L7, DECISIONS S14), Eaton RFRM `rfrm`, 3x MTA 0301491 `mta1`-`mta3`) with the ECU-switched relays seated in it, battery feed ring, fuel pump run to the trunk; the ECU coil wires, splices, CSB3, CAN (DEV), AntiTheft and EngineRoom-C ends arrive broken off |
| `ST185-HeavyDC.harness` | Heavy DC (Route 1) | trunk battery, RADLOK firewall pair, starter, 160 A alternator B+, engine-bay jump post, engine block ground; hands off to EngineRoom-C at the cabin PDB (breaks H1/H2/H3/H6a) |
| `ST185-CSB3.harness` | ECUMaster CSB3 | CSB3 plug, cruise stalk, clutch and brake switches, cruise ladder, the 8-channel brake / reverse optocoupler board inline at the plug (DECISIONS S17, S25); power, ground, reverse, LED and CAN wires arrive broken off |
| `ST185-A-engine.harness` | ECU connector A, engine | bulkhead A engine half to every A-letter engine device, plus the `IX_B_RAIL` spur (B-engine sensor +5V / Gnd Out) |
| `ST185-B-engine.harness` | ECU connector B, engine | bulkhead B engine half to every B-letter engine device and the ETB motor; the B sensors' +5V / Gnd Out come in on `IX_B_RAIL` |
| `ST185-CAN.harness` | CAN backbone | the only drawing with CAN H/L |
| `ST185-EngineRoom-C.harness` | Loom C | engine room, PDB (battery, RADLOK and ground studs; the fuse box is on CabinPower), EPS, the ex-J/B2 / R/B loads (headlamp and horn feeds to the device plugs; cabin-side landings at J/B1 / IE1 / blower / window feed as flying leads); the A4/A5 A/C device-side flying leads (VC coil - not fitted - and pressure switch, folded in from ST185-ACAmp-Spur 2026-10-11, new-wire runs, no factory engine-bay wire reused) |
| `ST185-WheelSpeed-Front.harness` | Front wheel speed | one Y harness: FL/FR drops to the front VRC endpoints, output to `IX_WS_FRONT` |
| `ST185-WheelSpeed-Rear.harness` | Rear wheel speed | one Y harness: RL/RR drops to the rear VRC endpoints, output to `IX_WS_REAR` |
| `ST185-RearFuel.harness` | Rear Fuel | fuel level sender behind `IX_FUEL_LVL` |
| `ST185-ClusterLED.harness` | Cluster warning LEDs | LED loom; C11/C12 taps are flying leads |
| `ST185-AntiTheft.harness` | Anti-theft | cabin |
| `ST185-RearLights.harness` | Rear lights (Route 15) | J/B No.1 1F tail / turn and S9 stop flying leads, reverse feed broken off from `k_rev` (CabinPower), R11 / R12 rear combination lamps, L1 license light, H6 high-mount stop light (hatch), one rear ground BL |

The four ECU loom files follow the ECU connector letter - the rule, its three allowed
crossovers are in `../RECONCILIATION-RULES.md` Rule 3 (the old Q-RAIL deviation is
closed: the injector/COP rails cross on bulkhead A c48 / c49). `validate_bulkhead_letter.py` enforces it; `audit_mating.py` checks A cabin cN
mates A engine cN and B mates B.

The only center-cluster portion in this repo is the CAN node, plus power and
ground to the cluster. Interior cluster wiring lives only in
`center-cluster-esp32-p4`. Do not add interior cluster circuits here.
`ST185-CAN` ends at its CAN-drop terminal.

The fuse box lives only in `ST185-CabinPower` (2026-10-11, Option B; slot map in
`../electrical/ENGINE-ROOM-POWER-REDISTRIBUTION.md` §8.1).
Loom C's old `gbx_body` glove-box body block and the PDB's fused AM1 / AM2 / OEM HOT
outputs moved there; EngineRoom-C keeps the cabin-side OEM ends (IE1, J/B1, the leads at the old R/B2 / R/B4
spots, A/C pressure switch; J/B2 and the R/Bs themselves are removed, R12) and reaches the box through broken-off pairs. The PDB keeps only
its battery, RADLOK and ground studs. Some wire ids still carry `pmu` (`w_pmu_hl` ...)
from the PMU-16 days - names only, not a PMU.

## Boundaries

How each kind of boundary is drawn is in `redesign/INTERFACES.md`. In short:

- **Inline interface** - a real connector pair, one half per harness, same cavity text
  on both. The four today: `IX_WS_FRONT`, `IX_WS_REAR` (DT 6-way), `IX_FUEL_LVL`
  (DT 2-way) and `IX_B_RAIL` (A-engine to B-engine sensor +5V / Gnd Out). `IX_AC_CTS`
  (A/C coolant switch deleted) and the pedal's `IX_APS` (folded into A-cabin 2026-10-11)
  are retired.
- **Broken-off wire** - a wire that runs between two harness files is drawn in both, each
  section ending at a `Loose` terminal (`br_<wire>`) whose note names the other file. The
  pairs are `interfaces.json` "breaks"; no device is drawn on two files and there are no
  cross-reference dummies (Rule 3, `validate_bulkhead_letter.py` L6 / L7).
- **Bulkhead** - one shared Deutsch DRB102 (`DRB12-102PAE-L018` receptacle / `DRB16-102SAE-L018`
  plug + `DRBF-1A` flange), one 102-position connector drawn WHOLE on every loom that uses it (A-cabin / B-cabin: the
  receptacle; A-engine / B-engine: the plug). A and B are only our names for its sections
  (connector-letter gate): each loom wires its own section and marks the other's cavities N/C
  with a "see ST185-<other>" note. See `redesign/DECISIONS.md`
  ("Bulkhead A/B + DTP replaced by a shared DRB102"). Real cavity numbers, sizes and
  spares: `DRB102-CAVITY-MAP.md` (gate `audit_mating.py` M8).
- **Shared connectors** - rule R10: drawn whole in every file, the other file's cavities N/C
  (https://docs.harness.design/component/connector) with a "see ST185-<other file>" note.
  Register the connector in `interfaces.json` "physicalPartGroups"; gate
  `audit_shared_connectors.py`. Today the only shared connector is the DRB102 bulkhead.
- **OEM flying lead** - a `Loose` terminal whose text is the EWD locator. No OEM housing
  is ever modelled or bought.
- **Device endpoint** - the VRCs are not drawn; each lead ends at a labelled `Loose`
  terminal (`VRC_REAR_IN_L +`).

## The pipeline

```
sot/channels.csv             <- pin SoT; new pin facts go here first
rebuild/*.harness            <- edit the harnesses here
interfaces.json              <- and the ownership facts with them
  |
  +-- check_all.py             runs every gate below, in order, all hard
        validate_sot.py            drawings vs the SoT
        sync_io_table.py --check   XTREMEX-IO-TABLE.html vs the SoT
        lint_v09.py                schema and references
        validate_ownership.py      every file registered; one owner per conductor and part
        validate_interfaces.py     inline interfaces are matched real pairs
        validate_wheel_speed.py    front/rear Y harnesses, interfaces, spurs
        verify_connectivity.py     every SoT signal pin reaches a device across boundaries
        validate_oem_endpoints.py  OEM points are flying leads with EWD locators
        audit_cavity_parts.py      contact or plug, never both
        audit_shields.py           docs/SHIELD-RULES.md
        audit_pin_names.py         drains only on A7/B17; one name per mating cavity
        audit_mating.py            A mates A, B mates B
        validate_bulkhead_letter.py ECU looms follow the connector letter (Rule 3)
        audit_bulkhead_pairs.py    no one-sided bulkhead cavity
        audit_bh_collisions.py     no two circuits on one cavity half
        buylist.py                 writes NEED-TO-BUY.md
        buildlist.py               writes HARNESS-BUILD-LIST.csv
```

Use it before every commit:

```
python docs/harness/check_all.py
```

`run_pipeline.bat` runs the same thing. `sync_io_table.py` without `--check` rewrites
the generated pin map in the IO table after a CSV change. `model.py` is the shared
reader: it loads the registry and builds one electrical graph across every harness
(bulkhead halves, interface halves, cross-references and VRC enclosures each collapse
to one node).

## Parts - how the gates count them

The parts rules are R38 (never guess a part number), R39 (library is the master), R44 / R49
(clean drawings, no unused parts), R48 (descriptions name the part) and R35 (wire part
numbers) in `redesign/DECISIONS.md`. The counting mechanics the gates apply:

1. A cavity holds a contact or a sealing plug, never both; a cavity wired in *any* harness
   gets a contact (`audit_cavity_parts.py`, `validate_interfaces.py`).
2. A connector drawn on more than one harness carries the same part everywhere and is counted
   on exactly one copy (`validate_ownership.py` O3, `buylist.py`).
3. A `br_` broken-off terminal has no part; each wire section is counted on its own harness.

Adding up the parts lists off the individual drawings by hand will over-order.
`NEED-TO-BUY.md` is the only correct total.

## Versioning

Files are not version-numbered. Git is the version history, and one folder means
one generation:

- a new generation gets a new folder, and the old one moves to `archive/` - only with
  Daniel's OK (R46: never auto-archive)
- nothing is ever copied sideways into the same folder with a suffix
- `-v2`, `-new`, `-final`, `-copy` in a filename is a bug, not a version
