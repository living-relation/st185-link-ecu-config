# Harness files - which one is current

Written 2026-09-22, rewritten 2026-09-27 for the harness redesign. Read this before
opening any loom.

**The wiring source of truth is `sot/channels.csv`** (every ECU pin and channel).
The looms below are the physical build and must agree with it; `check_all.py`
enforces that.

## The short answer

**`rebuild/` is the truth. Everything else is a copy, a build product, or history.**

| Folder / file | What it is | Edit it? |
|---|---|---|
| **`rebuild/`** | The 12 current harnesses. Human-readable JSON, what git diffs, what matches harness.design | **Yes - this is the source** |
| **`interfaces.json`** | Who owns what: physical harness per file, inline interface pairs, VRC endpoints, OEM flying leads with EWD locators, registered cross-references. harness.design rejects unknown keys, so this cannot live in the drawings | **Yes - with the drawings** |
| `min/` | Same documents, whitespace stripped, for upload to the harness.design project "ST185 harness design". The Free plan caps a harness at 100 connections, so every file must stay under 100 | No - `make_min.py` regenerates it |
| `redesign/` | Decision record, implementation plan, interface convention | Decisions only by agreement |
| `../../archive/2026-09-27-harness-redesign/` | The retired frozen baseline and legacy tools | No - history only |

## The 12 harnesses

Each file is one physical harness that gets built. Shared nets may cross a boundary; a
physical section of copper, a connector or a BOM line has one owner.

| File | Harness | Scope |
|---|---|---|
| `ST185-A-cabin.harness` | ECU connector A, cabin | ECU-A, cabin half of bulkhead A, fuse block, HCFB, A-triggered relays, APS, CSB3 plug, front wheel-speed spur, A/C coolant switch branch, fuel pump run, the +5V / Gnd Out / +8V / switched-12V splices |
| `ST185-B-cabin.harness` | ECU connector B, cabin | ECU-B, cabin half of bulkhead B, condenser fan relay, fuel level branch, rear wheel-speed spur, the front spur's FR core, the B legs of +5V / Gnd Out |
| `ST185-A-engine.harness` | ECU connector A, engine | bulkhead A engine half to every A-letter engine device |
| `ST185-B-engine.harness` | ECU connector B, engine | bulkhead B engine half to every B-letter engine device and the ETB motor |
| `ST185-CAN.harness` | CAN backbone | the only drawing with CAN H/L |
| `ST185-EngineRoom-C.harness` | Loom C | engine room, PDB, fuse blocks + relays, EPS, OEM J/B feeds (J/B2 dummy headers; the rest are flying leads) |
| `ST185-WheelSpeed-Front.harness` | Front wheel speed | one Y harness: FL/FR drops to the front VRC endpoints, output to `IX_WS_FRONT` |
| `ST185-WheelSpeed-Rear.harness` | Rear wheel speed | one Y harness: RL/RR drops to the rear VRC endpoints, output to `IX_WS_REAR` |
| `ST185-RearFuel.harness` | Rear Fuel | fuel level sender behind `IX_FUEL_LVL` |
| `ST185-ACAmp-Spur.harness` | A/C amplifier spur | receiving side of `IX_AC_CTS` to flying leads at the auto A/C amplifier |
| `ST185-ClusterLED.harness` | Cluster warning LEDs | LED loom; C11/C12 taps are flying leads |
| `ST185-AntiTheft.harness` | Anti-theft | cabin |

The four ECU loom files follow the ECU connector letter - the rule, its three allowed
crossovers and the one open deviation (Q-RAIL) are in `../RECONCILIATION-RULES.md`
Rule 3. `validate_bulkhead_letter.py` enforces it; `audit_mating.py` checks A cabin cN
mates A engine cN and B mates B.

The center cluster's own assembly harness lives in `center-cluster-esp32-p4`;
`ST185-CAN` ends at its CAN-drop terminal.

Loom C's `gbx_body` node (part `cp_gbx_body`) is the glove-box body block - a
second fuse block plus micro ISO relays - carrying the ex-J/B2 circuits plus the
CSB3 and device feeds. Some wire ids still carry `pmu` (`w_pmu_hl`, `w_pdb_pmu` ...)
from its PMU-16 days - names only, not a PMU.

## Boundaries

How each kind of boundary is drawn is in `redesign/INTERFACES.md`. In short:

- **Inline interface** - a real connector pair, one half per harness, same cavity text
  on both. The four today: `IX_WS_FRONT`, `IX_WS_REAR` (DT 6-way), `IX_AC_CTS`,
  `IX_FUEL_LVL` (DT 2-way).
- **Bulkhead** - HDP20 A and B, each half drawn on the harnesses that populate it.
- **OEM flying lead** - a `Loose` terminal whose text is the EWD locator. No OEM housing
  is ever modelled or bought.
- **Device endpoint** - the VRCs are not drawn; each lead ends at a labelled `Loose`
  terminal (`VRC_REAR_IN_L +`).
- **Registered reference** - a harness populating one cavity of a connector another
  harness owns (ECU pins, CSB3 cavities); listed in `interfaces.json` with the reason.

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
        audit_mating.py            A mates A, B mates B; A7 and B17 never joined
        validate_bulkhead_letter.py ECU looms follow the connector letter (Rule 3)
        audit_bulkhead_pairs.py    no one-sided bulkhead cavity
        audit_bh_collisions.py     no two circuits on one cavity half
        buylist.py                 writes NEED-TO-BUY.md
        buildlist.py               writes HARNESS-BUILD-LIST.csv
        make_min.py                writes min/  -> uploaded to harness.design
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

## Parts rules

1. **One cavity, one part.** A cavity holds a contact or a sealing plug, never
   both. A cavity wired in *any* harness gets a contact; a cavity wired in *no*
   harness gets a plug, in its own size. `audit_cavity_parts.py` and
   `validate_interfaces.py` fail the build otherwise.
2. **One physical connector, one part number, one counted copy.** A connector drawn
   on more than one harness (the bulkheads, shared engine devices) carries the same
   part everywhere and is counted on exactly one copy (`validate_ownership.py` O3).
3. **Cross-references claim nothing.** A `cp_xref` dummy has no part and no contact
   stamps, and every one is registered with its owner and reason.
4. **Never invent a part number.** A part not checked against the manufacturer gets
   `TBD ...` and the reason. Current examples: the RADLOK pass-through, the A/C
   coolant switch.

Adding up the parts lists off the individual drawings by hand will over-order.
`NEED-TO-BUY.md` is the only correct total.

## Versioning

Files are not version-numbered. Git is the version history, and one folder means
one generation:

- a new generation gets a new folder, and the old one moves to `archive/`
- nothing is ever copied sideways into the same folder with a suffix
- `-v2`, `-new`, `-final`, `-copy` in a filename is a bug, not a version
