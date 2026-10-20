# ECU channel settings (`sot/channels.csv`)

The ONE wiring source of truth is `docs/harness/MASTER-wirelist.csv` (DECISIONS R221). `channels.csv` keeps only the ECU
channel settings (type, pull-up, direction, tune / CAN data) and the pin each channel owns; it holds no net and no loom.
`python docs/harness/tools/check_wiring.py` compares its live pins with the master both ways and checks every ECU pin's
class against the Link G4X Quick Start Guide (R212). `XTREMEX-IO-TABLE.html` is its visual face:
`check_wiring.py --write-io-table` rewrites the table's generated pin map, and the plain run fails if the table is stale.
No script writes this file.

## The rule

A channel's identity comes from the pin that owns it (R45, `docs/RECONCILIATION-RULES.md` Rule 3). On the ECU that is the
Link G4X XtremeX pin: the pin decides what the channel can physically do (pull-up, drive type, voltage range). ECU pins are
fixed and never move. Device-owned pins live in `docs/devices/SENSOR-AND-ACTUATOR-REFERENCE.md`; for everything else the
owner is the device at the end that cannot move (the VR conditioner owns the raw wheel-speed pairs, the A/C amplifier the
ambient sensor).

## Columns

| column | meaning |
| --- | --- |
| `owner` | ECU, VRC, ACAMP, PWR, MRS - who defines this pin |
| `channel` | the PCLink channel name (e.g. `DI 3`, `Aux 7`, `Gnd Out`) |
| `conn` / `pin` | the owning connector and its pin, numbered exactly as the maker numbers it (numbers or letters, never signs) |
| `label` | what the pin does |
| `class` | `signal` `rail` `screen` `power` `ground` `spare` `nc` |
| `dir` / `type` / `pullup` | direction, PCLink type, the pull-up fitted (not what is available) |
| `status` | `set` `proposed` `spare` `tbd` `nc` |
| `source` | QSG-IO, QSG-loom, QSG-comms, EWD page, or a dated Daniel lock |
| `notes` | free text |

## Classes

- `signal` - one circuit, one name.
- `rail` - +5 V, +8 V, Gnd Out A / B, ECU ground: shared by many devices.
- `screen` - A7 and B17: **drain current only**; no signal, sensor return or power ground ever lands there.
- `spare` / `nc` - a master row that wires one of these fails the gate.

## Unknown means TBD

An unknown pin stays blank (status `tbd`) until a document says otherwise - never invent a pin number. ACT is A18 pin 11
(1992 EWD132U A17-11).
