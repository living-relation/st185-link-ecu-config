# Fuel hanger - how it was made

- **Tool:** build123d (Python, OpenCascade), run in WSL with the handbuilt-models `.venv`. No Fusion document.
- **Starting point:** the fairsolid build123d sources `C:\projects\active\fairsolid\runs\fuel_hanger_billet_1014\rev7\hanger_billet.py` and `rev8\` (the rejected M5 through-tap). Those folders stay untouched as history.
- **This release (2026-10-17, Dan's N6 decision, option 2):** the bolt-on lug block is machined integral with the top flange; the 2 M5 block screws and 2 dowels are gone. Build: `python fuel_hanger.py` (writes `fuel-hanger-*.step` + `fuel-hanger-report.json` beside it). Checks: `python check_flange.py`. Drawings: `make_drawings.py <flange|strut|foot|saddle>` with SteveCAD's build123d drawing engine (`stevecad-tools/drawing`).
- **Rev letters (counted per part):** each model's letter = its number of releases in the fairsolid rev folders (A first, skip I, L, O, Q): **flange G** (changed now; 6 earlier releases A-F), **strut E**, **foot D**, **saddle C** (unchanged, not bumped), lug block FH-102 obsolete at **A**. Evidence per part: `cad/DRAWING-REVS.md`. Filenames carry no rev.
