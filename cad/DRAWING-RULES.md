# Drawing rules (st185 shop drawings)

Rules every shop drawing in this repo follows. Decisions are in
`docs/harness/redesign/DECISIONS.md`; rev letters are in `cad/DRAWING-REVS.md`.

| Rule | Source |
|---|---|
| Never show hidden lines in any view. Center marks and center lines for holes and radii are kept (and added where useful). | R150 (Dan 2026-10-17) |
| The model drives the rev letter; drawing and model letters always match. Letters run A-Z skipping I, L, O, Q, then AA, AB, ... (R152); Rev A only for a brand-new model. Drawing-only (clerical) changes to a released drawing add .01, .02 ...; a model change bumps the letter. | R147 |
| Redlines go on the drawing first, then the model is fixed, then the drawing is regenerated from the model. | R147 |
| The model is the master: every model change regenerates its drawing (same PR); a wrong drawing is fixed in the model or its source script, never by hand-editing the drawing. Drawing rev = model letter, or model letter + .NN for a clerical drawing-only change; models never get decimals. Gate `cad/check_drawings_current.py` (in `check_all.py`); after regenerating a drawing run `python cad/check_drawings_current.py --update <part no>`. | R183 |
| No rev in file names; the letter lives in the title block and the register. | R148 |
| Rev log table, top right of sheet 1: Rev / Description / By / Date (dd/mm/yy), from the model's `<part no>.REVLOG.md` beside its STEP (plain `REVLOG.md` only when the folder holds one STEP). One row per PR / release, no clerical rows, Rev A = "Initial", newest 6 rows shown, full history kept in the file; title-block letter = newest row. | R152 |
| No visible mesh triangles, facet or seam lines in any drawing or render; parts look like smooth machined bodies. | R152 |
| Minimum wall thickness applies to structural / critical features only; anything questionable is flagged for Dan. | R151 |
| Model files are STEP only; STL only as a print-job file for a printed part. | R152 |
| Every model says what made it (`MADE-WITH.md` + register column). | R149 |
| Edges the CAD can't break cleanly are a drawing note, not modelled. | R138 |
