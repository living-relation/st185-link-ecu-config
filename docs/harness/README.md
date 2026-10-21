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
  - **Kept OEM:** every cabin wire (cowl, instrument panel, floor, door, seat, console and luggage room wires); cabin
    J/B No.1 and No.3 (what a kept J/B feeds stays fed from it: fuse, relay, pin); the rear lights; both A/C amps (A15
    and the auto A/C amp A31 / A32, A23); the four wheel speed sensors (they feed the Link). Forward of the firewall
    only 6 in OEM pigtails stay, spliced to new wire at the headlights, turn / hazard and clearance / corner lamps,
    pop-up motors, ambient air temp sensor and wiper motor (B9).
  - **Removed (never a circuit source):** the Engine Wire; the Engine Room Main Wire (outer loop) and every Cowl Wire
    leg forward of the firewall, except those pigtails; every OEM relay and fuse box except J/B No.1 / No.3: J/B No.2,
    R/B No.2, No.3, No.4 and No.5, the ABS relay box (Dan 2026-10-21; their jobs are in the glove-box POWER / LOGIC
    boxes); the OEM engine ECU and igniter; every SRS crash sensor and SRS computer; the ABS computer and actuator; the
    brake fluid level switch; the fog lights (the car has none). Each live wire that crossed from a removed part into a
    kept harness gets one row in the master: re-feed from the cabin side, or remove. A dead OEM wire comes out of its
    harness back to its last live point (splice, plug or box); nothing is left cut and capped (Dan 2026-10-21; goes into
    B5 at the rules walk-through). The R/B No.4 socket keeps two live leads as pigtails: the key START wire (Link start
    request) and the clutch switch wire (CSB3).
  - **New wire** (routes: `routes/ROUTE-16-ENGINE-MAIN.html` lines 1-9, `routes/ROUTE-17-FRONT.html` lines 10-13): the
    engine harness (Link to every engine sensor and actuator; through bulkhead A); power from the trunk battery up the
    passenger side to the glove-box boxes, then out through the RH fender grommet for engine-bay loads; the front run
    (inside the RH fender, then along the underside of the radiator support) to every front device; the driver fender
    run (driver kick pass-through) to the wiper motor and the alarm siren; one mini harness per front wheel speed sensor
    to the VRC enclosure by the ECU; the fuel pump circuit; one dash feed for the cluster, LEDs and RealDash Pi; CAN;
    the alarm add-on; power taps. A spare relay circuit (was fog) runs to the old fog-lamp spots, ends insulated.
    Engine-bay jump studs at the old battery spot are optional (owning harness open).
  - **Connectors:** the new wire mates only with each device's own connector (Dan has the mating plugs); no new inline
    connector anywhere on a run, and none added at the device, unless one later helps install or maintenance (fewer
    connectors, fewer failure points; Dan 2026-10-21).
  - Kept OEM ground points (where a high-current load may ground, B10): EA (M8 studs), EB, EC, ID, IE / IF, IG.
- Pin authority for OEM ends: the 1993 ST185 EWD (Dan 2026-10-20, DECISIONS R16): the 1993 TIS EWD pages in the
  `st185-celica-repair-manual` repo. The 1990 ST185 All-Trac book and the 1992 Celica EWD132U are reading aids only; an
  end still sourced from them is re-checked against 1993 (`docs/OPEN-ITEMS.md` row 156). The public PDF labelled EWD160U
  is the FWD AT180 / ST184 book: never use its pin numbers. Factory snips: `docs/electrical/ewd-snips/`.
- Before first power-up, with the battery isolated: ohmmeter from each cabin landing (J/B1, IE1, the old R/B2 / R/B4
  leads, blower, ignition switch) to its named load.
