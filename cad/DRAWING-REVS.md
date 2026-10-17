# Drawing / model revision register

Rules (Dan, 2026-10-17): each part model's letter comes from counting its past RELEASES in its own history; the first release is A; letters skip I, L, O, Q (this overrides converting old rev numbers). A drawing always carries its model's letter. A part that did not change keeps its letter.
Drawing-only clerical changes (notes, added views or sheets, no change to fit / form / function) add .01, .02, ... (e.g. G.01); a model change takes the next letter and resets the decimal.
Redlines go on the drawing first, then the model is fixed, then the drawing is regenerated from the model. Filenames carry no rev.

Fuel hanger evidence: the fairsolid run `C:\projects\active\fairsolid\runs\fuel_hanger_billet_1014\` - `rev1` = the run root folder, then `rev2`..`rev8`; each folder is one release. `runs/` is gitignored in fairsolid, so there is no git history for it; a part counts as released in a folder when its model changed there (volume / bounding box in that folder's `hanger_report.json`).

| Item | Part no. | Model | Rev | Date | Change | Evidence (counted releases) | Files |
|---|---|---|---|---|---|---|---|
| Fuel hanger - flange (integral lug) | ST185-FH-101 | `cad/fuel-hanger/fuel_hanger.py` | G | 2026-10-17 | Lug block machined integral with the top flange (N6 option 2); M5 block screws + dowels deleted; 13 through-holes only | top plate changed in fairsolid rev1 (97.18 cm3, lug integral) = A, rev2 (73.31) = B, rev3 (87.60; rev4/5 identical) = C, rev6 (82.66) = D, rev7 (76.01, bolt-on lug) = E, rev8 (75.96, M5 thru, rejected) = F; this release (89.94) = G | `cad/fuel-hanger/drawings/ST185-FH-101.pdf` / `.dxf` |
| Fuel hanger - lug block | ST185-FH-102 | - | A (obsolete) | 2026-10-17 | Merged into FH-101 rev G | only in rev7 (12.77 cm3) = A; rev8 identical | - |
| Fuel hanger - strut | ST185-FH-103 | `cad/fuel-hanger/fuel_hanger.py` | E | 2026-10-14 | Not changed; drawing issued at its current letter | rev1 (71.77; rev2 identical) = A, rev3 (71.88) = B, rev4 (71.40; rev5 identical) = C, rev6 (60.28) = D, rev7 (64.66; rev8 identical) = E; this build identical to rev7 = E (not bumped) | `cad/fuel-hanger/drawings/ST185-FH-103.pdf` / `.dxf` |
| Fuel hanger - foot | ST185-FH-104 | `cad/fuel-hanger/fuel_hanger.py` | D | 2026-10-14 | Not changed; drawing issued at its current letter | rev1 (24.20; rev2/3 identical) = A, rev4 (24.88; rev5 identical) = B, rev6 (19.21) = C, rev7 (20.00; rev8 identical) = D; this build identical to rev7 = D (not bumped) | `cad/fuel-hanger/drawings/ST185-FH-104.pdf` / `.dxf` |
| Fuel hanger - pump saddle | ST185-FH-105 | `cad/fuel-hanger/fuel_hanger.py` | C | 2026-10-14 | Not changed; drawing issued at its current letter | rev1 (24.15; rev2/3 identical) = A, rev4 (24.18) = B, rev5 (15.95, band-clamp saddle; rev6-8 identical) = C; this build identical to rev7 = C (not bumped) | `cad/fuel-hanger/drawings/ST185-FH-105.pdf` / `.dxf` |
