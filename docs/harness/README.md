# Harness and wiring - what is in this folder

**The ONE wiring source of truth is `MASTER-wirelist.csv`** (DECISIONS R221): one row per wire, FROM end to TO end, for
every harness. `sot/channels.csv` keeps only the ECU channel settings and is checked against it. Every rule Daniel has set
is in `redesign/DECISIONS.md` "Binding rules B1-B30"; this page restates none of them (it holds the factory-wiring detail
that B9 points to).

| Path | What it is | Edit it? |
|---|---|---|
| `MASTER-wirelist.csv` | every wire, cavity, splice, mate and spare of every harness | **Yes - the only wiring file you edit** |
| `drawings/` | generated: each drawing set as three single-page PDFs (`<set>-schematic.pdf`, `<set>-layout.pdf`, `<set>-pinout.pdf`), each one big sheet sized to its content with its own title block and rev log and the DRB102 insert-face map | No - re-run the generator |
| `tools/build_drawings.py` | the drawing generator; a drawing set is `tools/<set>.layout.json` (physical tree, harnesses in the set) + `tools/<set>.revs.json` (title block, rev log) | The layout and rev files, yes |
| `tools/check_wiring.py` | the ONE wiring check (also writes the IO table pin map with `--write-io-table`) | Only to add a rule |
| `routes/` | Dan's approved route drawing per harness (one HTML each, current version only) | Only from Dan's markup |
| `redesign/DECISIONS.md` | every binding rule (B1-B30) and the retire map of the old R / S numbers | Only for a new Dan rule |

Generated views that are not committed (R221): the pinout `.xlsx` and thumbnails land in `out/` (gitignored).

## Change the wiring

1. Edit the rows in `MASTER-wirelist.csv` (pins exactly as the maker numbers them; a part number not confirmed by a maker
   document is `TBD`, never guessed).
2. `python docs/harness/tools/check_wiring.py` (add `--tbd` to list every TBD cell).
3. `python docs/harness/tools/build_drawings.py <set>` for a drawing set that holds the harness, and
   `python docs/sourcing/build_project_bom.py` for the shopping list.
4. `python tools/check_all.py` before the commit (CI runs it, plus `check_wiring.py --self-test`).

## Harnesses in the master

`AB-cabin` and `AB-engine` (the ECU harness, loom A and B merged, R220), `CabinPower`, `HeavyDC`, `EngineRoom-C`, `CAN`,
`CSB3`, `ClusterLED`, `AntiTheft`, `RearFuel`, `RearLights`, `WheelSpeed-Front`, `WheelSpeed-Rear`. All 13 are drawn by
the generator as ONE drawing set, `ST185-harness` (`drawings/ST185-harness-schematic.pdf`, `-layout.pdf`, `-pinout.pdf`;
layout tree `tools/ST185-harness.layout.json`). Part makers and descriptions (AWG ranges) the BOM and the check read:
`docs/sourcing/harness-parts.csv`.

## Factory wiring facts (OEM ends)

- What stays and what goes (DECISIONS B1 / B9, surgical rewire, Dan 2026-10-20):
  - **Kept OEM:** cowl, instrument panel, floor, door, seat, console and luggage room wires; cabin J/B No.1 and No.3 (what
    a kept J/B feeds stays fed from it: fuse, relay, pin); the Engine Room Main Wire outer loop (headlights, turn and
    clearance lamps, horns, fans, washer); the rear lights; both A/C amps (A15 and the auto A/C amp A31 / A32, A23); the
    four wheel speed sensors (they feed the Link). Every branch of a kept harness that runs into the engine area is cut
    and its job moves into the new engine harness.
  - **Removed (never a circuit source):** the Engine Wire; J/B No.2, R/B No.2-5 and the A/C clutch relay box; the OEM
    engine ECU and igniter; every SRS crash sensor and SRS computer; the ABS computer and the ABS actuator (solenoid
    module). Each wire that crossed from a removed part into a kept harness gets one row in the master: cut and cap,
    reuse, or re-feed (B5).
  - **New wire:** the engine harness (Link to every engine sensor and actuator), the fuel pump circuit, one dash feed
    for the cluster, LEDs and RealDash Pi (bypassing the dash wiring), CAN, the alarm add-on, and power taps.
  - Kept OEM ground points (where a high-current load may ground, B10): EA (M8 studs), EB, EC, ID, IE / IF, IG.
- Pin authority for OEM ends: the 1993 ST185 EWD (Dan 2026-10-20, DECISIONS R16): the 1993 TIS EWD pages in the
  `st185-celica-repair-manual` repo. The 1990 ST185 All-Trac book and the 1992 Celica EWD132U are reading aids only; an
  end still sourced from them is re-checked against 1993 (`docs/OPEN-ITEMS.md` row 156). The public PDF labelled EWD160U
  is the FWD AT180 / ST184 book: never use its pin numbers. Factory snips: `docs/electrical/ewd-snips/`.
- Before first power-up, with the battery isolated: ohmmeter from each cabin landing (J/B1, IE1, the old R/B2 / R/B4
  leads, blower, ignition switch) to its named load.
