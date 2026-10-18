# Billet fuel hanger (ST185)

In-tank pump hanger, billet 6061-T6, for the Walbro F90000295. build123d model, in this repo since 2026-10-17 (flange rev G).

| File | What |
|---|---|
| `fuel_hanger.py` | flange build source (run in WSL, handbuilt-cad `.venv`); writes the flange + fit-check STEP files + `fuel-hanger-report.json` |
| `build_holder.py`, `pump_holder.py`, `pumpmount.py` | option B holder (Dan B9, 2026-10-17): strut FH-103, foot FH-104, saddle FH-105 and the assembly; run after `fuel_hanger.py`; `holder-report.json`, `holder-handcheck.json` (M4 joint hand check), `checks_revH.json` |
| `fuel-hanger-*.step` | flange (integral lug), strut, saddle, foot, assembly, and fit-check envelopes (gitignored, local in the main checkout, R67) |
| `check_flange.py`, `check-results.json` | flange checks: valid solid, STEP round-trip, 13 through-holes, strut / valve fit |
| `drawings/` | shop drawings (SteveCAD build123d drawing engine): ST185-FH-100 assembly, FH-101 flange, -103 strut, -104 foot, -105 saddle (PDF, DXF, PNG preview); made by `cad/drawings/specs_1017.py` (FH_ORDER) and `cad/drawings/aspecs.py` (fuel_hanger). The older `make_drawings.py` (pre-option-B letters, old saddle file) was retired 2026-10-18 (R46) |
| `MADE-WITH.md` | how it was made and where it came from (fairsolid rev 7/8) |
| `trimetric.png` | hub picture (`cad/render_trimetric.py`) |

**Flange rev G vs fairsolid rev 7:** the bolt-on lug block (FH-102 rev A, now obsolete) is machined integral with the top flange; the 2 M5 block screws and 2 dowel pins are deleted. The flange keeps exactly its 13 original through-holes (2 AN bulkheads, 2 isolated electrical studs, 9 flange screws); nothing else breaks the sealing face. Strut, check valve, pass-throughs and the 2 x dia 6.6 M6 strut cross-holes are unchanged.

Rev letters: each part's letter = its counted releases (flange G, strut F, foot E, saddle D, assembly K); drawings carry the model letter (letters skip I, L, O, Q; drawing-only clerical changes add .01, .02...). Filenames carry no rev. Register: `cad/DRAWING-REVS.md`.
