# Fuel hanger - how it was made

- **Tool:** build123d (Python, OpenCascade), run in WSL with the handbuilt-models `.venv`. No Fusion document.
- **Starting point:** the fairsolid build123d sources `C:\projects\active\fairsolid\runs\fuel_hanger_billet_1014\rev7\hanger_billet.py` (model rev G) and `rev8\` (the rejected M5 through-tap). Those folders stay untouched as history.
- **Rev H (2026-10-17, Dan's N6 decision, option 2):** the bolt-on lug block is machined integral with the top flange; the 2 M5 block screws and 2 dowels are gone. Build: `python fuel_hanger.py` (writes `fuel-hanger-*.step` + `fuel-hanger-report.json` beside it). Checks: `python check_flange.py`. Drawings: `make_drawings.py <flange|strut|foot|saddle>` with SteveCAD's build123d drawing engine (`stevecad-tools/drawing`).
- **Rev letters:** the model drives the rev (fairsolid rev 7 = G, this = H; letters skip I, L, O, Q). Filenames carry no rev; the rev is in the title blocks and `cad/DRAWING-REVS.md`.
