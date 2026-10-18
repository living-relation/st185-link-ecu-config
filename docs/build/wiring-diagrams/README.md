# Assembly wiring diagrams

Simple block diagrams of the fuse box assemblies and of every OEM box where we splice into the factory loom (Dan 2026-10-18, DECISIONS R180).
Generated, never drawn by hand: `python docs/build/wiring-diagrams/build_wiring_diagrams.py` (PDFs need `pip install pymupdf`).

| File | What |
|---|---|
| `fusebox-wiring.svg` / `.pdf` | ONE diagram: POWER box, LOGIC box, battery relay block. Every fuse and relay with its cavity / pin labels, every wire as one line (id, gauge, colour), exits end at a stub naming the far end (R156). One page, A1 size at 1:1. |
| `fusebox-wiring-A3-tiles.pdf` | The same diagram in three A3 landscape tiles (POWER, LOGIC, battery block) at 85 %, for the printer. |
| `oem-jb1.svg` J/B No.1 | LH kick panel: plugs 1I, 1H, 1F. |
| `oem-ie1.svg` IE1 cowl plug | LH kick panel: 17 leads. |
| `oem-rb2.svg` / `oem-rb4.svg` | Old R/B No.2 (LH kick) and R/B No.4 (RH kick) positions - blocks removed, factory leads spliced. |
| `oem-jb3.svg` J/B No.3, `oem-ig2.svg` IG2 plug | Behind the combination meter / under the ECU. |
| `oem-gnd.svg` | Kick-panel body grounds ID and IG. |
| `oem-junction-boxes.pdf` | All OEM sheets in one PDF. |
| `MISMATCHES.md` | Written on every run: where the SoT chain and the looms disagree. Empty list = checked and clean. |

## Where the facts come from (R45: the looms are not a source of truth)

- Fuse / relay list and ratings: `cad/fusebox/src/spec.py` (`AMI_ROWS`, `MINI_COLS`, `MICRO_POS`, `F7_POS`).
- Relay pins: `sot/channels.csv` (PWR rows).
- OEM splices (connector, pin, OEM colour, EWD page, method): `docs/harness/interfaces.json` `flyingLeads`.
- Wire id, gauge, insulation colour, ident bands, far-end label: read from `docs/harness/rebuild/*.harness` for lack of another home, and cross-checked
  against the three sources above; a disagreement goes to `MISMATCHES.md`.

## Layout notes

- Overhead block view, not to scale, front of the car at the top. The three assemblies are stacked so every wire label has room.
- Rows are grouped for readable wires, not in physical order; every fuse and relay carries its cavity number (`BUS1-n`, `BUS2-n`, `AMI IN-n`, `AMI OUT-n`).
- A line that crosses another with a gap does not connect to it.
- The OEM sheets show only the plugs and cavities we splice. Splices into DEVICE plugs (switches, lamps, motors, A/C amplifier, combination meter)
  are not junction boxes and have no sheet; `MISMATCHES.md` lists them.
- Wire ends on far side stubs use the R156 text of the loom end (device and pin, connector and pin, or stud and where it is).

Files: `wd_data.py` (data + cross-checks), `wd_svg.py` (SVG writer), `fusebox_sheet.py` + `fusebox_assembly.py` (fuse box sheet), `oem_sheets.py`
(OEM sheets), `pdf_out.py` (PDF), `build_wiring_diagrams.py` (entry point; `--check` for staleness, also run warn-only by `docs/harness/check_all.py`).
