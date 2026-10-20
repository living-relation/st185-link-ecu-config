# Harness and wiring - what is in this folder

**The ONE wiring source of truth is `MASTER-wirelist.csv`** (DECISIONS R221): one row per wire, FROM end to TO end, for
every harness. `sot/channels.csv` keeps only the ECU channel settings and is checked against it. Every rule Daniel has set
is in `redesign/DECISIONS.md` "Binding rules from Daniel"; this page restates none of them.

| Path | What it is | Edit it? |
|---|---|---|
| `MASTER-wirelist.csv` | every wire, cavity, splice, mate and spare of every harness | **Yes - the only wiring file you edit** |
| `drawings/` | generated: each drawing set as three single-page PDFs (`<set>-schematic.pdf`, `<set>-layout.pdf`, `<set>-pinout.pdf`), each one big sheet sized to its content with its own title block and rev log and the DRB102 insert-face map | No - re-run the generator |
| `tools/build_drawings.py` | the drawing generator; a drawing set is `tools/<set>.layout.json` (physical tree, harnesses in the set) + `tools/<set>.revs.json` (title block, rev log) | The layout and rev files, yes |
| `tools/check_wiring.py` | the ONE wiring check (also writes the IO table pin map with `--write-io-table`) | Only to add a rule |
| `routes/` | Dan's approved route drawing per harness (one HTML each, current version only) | Only from Dan's markup |
| `rebuild/` | the frozen harness.design files and part library (`ST185.harnesslib`) of the harnesses the generator does not draw yet; `full_text.json` puts back their long names for `cad/fusebox/src/wiring_sim.py`. Deleted once the generator draws every harness | No (frozen) |
| `redesign/DECISIONS.md` | every binding rule | Only for a new Dan rule |

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
layout tree `tools/ST185-harness.layout.json`). The frozen `rebuild/` files stay only until the part data the BOM and the
tools still read from them moves out (OPEN-ITEMS row 149).

## Factory wiring facts (OEM ends)

- Pin authority for OEM ends: the 1990 ST185 All-Trac EWD (the All-Trac book), cross-checked against the 1992 Celica
  EWD132U. The public PDF labelled EWD160U (1993) is the FWD AT180 / ST184 book: never use its pin numbers. The 1993 TIS
  EWD pages are in the `st185-celica-repair-manual` repo. Factory snips: `docs/electrical/ewd-snips/`.
- Before first power-up, with the battery isolated: ohmmeter from each cabin landing (J/B1, IE1, the old R/B2 / R/B4
  leads, blower, ignition switch) to its named load.
