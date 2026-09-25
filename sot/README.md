# Source of truth

`channels.csv` is the root of the harness tree and the single wiring source of
truth (Daniel, 2026-09-25). Every drawing is validated against it, never the
other way round. `XTREMEX-IO-TABLE.html` is its visual face:
`python docs/harness/sync_io_table.py` rewrites the table's generated pin map, and
`--check` (run by `check_all.py`) fails if any row disagrees with this file.

Run the gate:

```
python docs/harness/validate_sot.py
```

It also runs first inside `python docs/harness/check_all.py`.

## The rule

A channel's identity comes from the pin that owns it. For anything on the ECU
that is the Link G4X XtremeX pin, because the pin decides what the channel can
physically do - its pull-up, its drive type, its voltage range. A sensor cannot
be "moved to loom A" as a matter of taste; it lives on whichever loom carries
its ECU pin. For everything else the owner is the device at the end that cannot
move: the A/C amplifier owns the ambient sensor, the VR conditioner owns the
raw wheel-speed pairs, the fuse box owns the OEM power splices.

## Columns

| column | meaning |
| --- | --- |
| `owner` | ECU, VRC, ACAMP, PWR, MRS - who defines this pin |
| `conn` / `pin` | the owning connector and cavity, exactly as the drawings spell them |
| `net` | the canonical net name; the same net on two rows means one electrical node |
| `class` | `signal` `rail` `screen` `power` `ground` `spare` `nc` |
| `pullup` | what is fitted, internal or external - not what is available |
| `shield` | which screen pin this signal's drain terminates on, or `own` |
| `loom` | which harness carries the conductor at the owner's end |
| `status` | `set` `proposed` `spare` `tbd` `nc` |
| `source` | QSG-IO, QSG-loom, QSG-comms, EWD page, harness file, or a dated Daniel lock |

## Classes and the pin-name rule

- `signal` - one circuit, one name; a bulkhead cavity carrying it must use the
  same name on both halves of the mating pair.
- `rail` - `P5V`, `P8V`, `GNDOUT`, `GND_ECU`. Shared by many devices, so the
  same-name rule does not apply cavity by cavity.
- `screen` - `SHIELD_A` (A7) and `SHIELD_B` (B17). **Drain current only.** No
  signal, no 5V return, no power ground may ever land on these two pins, and
  the two are never bridged to each other.
- `spare` / `nc` - a drawing that wires one of these fails the gate.

## TBD means TBD

Two rows are `tbd` (the A/C amp's ambient-sensor return and ACT terminal numbers).
They stay blank until a document says otherwise - do not invent a pin number to
make a drawing look finished.
