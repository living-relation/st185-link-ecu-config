# Made with - `cad/drb102-plate/`

What made each model file in this folder (Dan 2026-10-17, DECISIONS R149). The model files are gitignored and live in the main checkout (R67); this note is tracked.
Source: the STEP / STL header, the build scripts and the git history. "unconfirmed" = not proven, never guessed. Register for all of `cad/`: [`cad/DRAWING-REVS.md`](../DRAWING-REVS.md).

| File | Made with | Evidence | Note |
|---|---|---|---|
| `DRB102-firewall-plate-assembly.step` | CadQuery + build123d | STEP header: Open CASCADE; `build_DRB102_plate.py` (CadQuery: plate, O-ring, firewall reference, screw heads), then `build_DRB102_assembly.py` (build123d) | The receptacle, flange and plug are TE's own models (`cad/vendor/te/DRB12-102PAE-L018`, `DRBF-1A`, `DRB16-102SAE-L018`, `cad/vendor/INDEX.md`), placed by contact search; they replace the envelope boxes (R184). |
| `DRB102-firewall-plate.step` | CadQuery | STEP header: Open CASCADE 7.9; `build_DRB102_plate.py` imports cadquery; `cad/drb102-plate/build_DRB102_plate.py` (CadQuery) |  |
