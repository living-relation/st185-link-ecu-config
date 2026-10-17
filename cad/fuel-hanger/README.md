# Billet fuel hanger (ST185)

In-tank pump hanger, billet 6061-T6, for the Walbro F90000295. build123d model, in this repo since 2026-10-17 (flange rev G).

| File | What |
|---|---|
| `fuel_hanger.py` | build source (run in WSL with the handbuilt-cad `.venv`); writes the STEP files + `fuel-hanger-report.json` |
| `fuel-hanger-*.step` | flange (integral lug), strut, saddle, foot, assembly, and fit-check envelopes (gitignored, local in the main checkout, R67) |
| `check_flange.py`, `check-results.json` | flange checks: valid solid, STEP round-trip, 13 through-holes, strut / valve fit |
| `make_drawings.py`, `drawings/` | shop drawings (SteveCAD build123d drawing engine): ST185-FH-101 flange, -103 strut, -104 foot, -105 saddle (PDF, DXF, PNG preview) |
| `MADE-WITH.md` | how it was made and where it came from (fairsolid rev 7/8) |
| `trimetric.png` | hub picture (`cad/render_trimetric.py`) |

**Flange rev G vs fairsolid rev 7:** the bolt-on lug block (FH-102 rev A, now obsolete) is machined integral with the top flange; the 2 M5 block screws and 2 dowel pins are deleted. The flange keeps exactly its 13 original through-holes (2 AN bulkheads, 2 isolated electrical studs, 9 flange screws); nothing else breaks the sealing face. Strut, check valve, pass-throughs and the 2 x dia 6.6 M6 strut cross-holes are unchanged.

Rev letters: each part's letter = its counted releases (flange G, strut E, foot D, saddle C); drawings carry the model letter (letters skip I, L, O, Q; drawing-only clerical changes add .01, .02...). Filenames carry no rev. Register: `cad/DRAWING-REVS.md`.
