# Drawing / model revision register

Rules (Dan, 2026-10-17): the model drives the rev letter; a drawing always carries its model's letter. Letters start at A and skip I, L, O, Q.
Drawing-only clerical changes (notes, added views or sheets, no change to fit / form / function) add .01, .02, ... (e.g. H.01); a model change takes the next letter and resets the decimal.
Redlines go on the drawing first, then the model is fixed, then the drawing is regenerated from the model. Filenames carry no rev.

| Item | Part no. | Model | Rev | Date | Change | Files |
|---|---|---|---|---|---|---|
| Fuel hanger - flange (integral lug) | ST185-FH-101 | `cad/fuel-hanger/fuel_hanger.py` | H | 2026-10-17 | Lug block machined integral with the top flange (N6 option 2); M5 block screws + dowels deleted; 13 through-holes only | `cad/fuel-hanger/drawings/ST185-FH-101.pdf` / `.dxf` |
| Fuel hanger - lug block | ST185-FH-102 | - | obsolete at H | 2026-10-17 | Merged into FH-101 | - |
| Fuel hanger - strut | ST185-FH-103 | `cad/fuel-hanger/fuel_hanger.py` | H | 2026-10-17 | Reissued with model rev H (part unchanged from rev G) | `cad/fuel-hanger/drawings/ST185-FH-103.pdf` / `.dxf` |
| Fuel hanger - foot | ST185-FH-104 | `cad/fuel-hanger/fuel_hanger.py` | H | 2026-10-17 | Reissued with model rev H (part unchanged from rev G) | `cad/fuel-hanger/drawings/ST185-FH-104.pdf` / `.dxf` |
| Fuel hanger - pump saddle | ST185-FH-105 | `cad/fuel-hanger/fuel_hanger.py` | H | 2026-10-17 | Reissued with model rev H (part unchanged from rev G) | `cad/fuel-hanger/drawings/ST185-FH-105.pdf` / `.dxf` |
