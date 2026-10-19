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
| No notes about things that are not in the model: no edge-break notes (also out of the tolerance block), nothing "not modelled". Replaces R138's drawing note. | R191 |
| Bought parts come from the real maker STEP (`cad/vendor/`), never an envelope model; no note says "envelope". | R184 |
| No pin / socket gender notes: gender belongs to the connector shell installed. | R185 |
| A balloon only where its part is clearly visible, its leader on that part; hidden parts are ballooned in an exploded or alternate view. | R186 |
| Tangent edges show in every trimetric view. | R187 |
| Balloons never overlap or crowd. | R188 |
| Fuse boxes: every fuse and relay has a note label beside its balloon naming its circuit or device (from the SoT). | R189 |
| Every harness wire landing on a fuse box carries its harness-drawing wire-end label (R156). | R190 |
| Change notes (what was fixed, markup dates, R / PR numbers) go in the rev log, never in NOTES. | R192 |
| Assembled views balloon only the primary parts (enclosure, lid). | R193 |
| Never label a screw that is not in the model; hidden screws go in an exploded view with dotted lines. | R194 |
| Notes are for a shop machinist: ELI5, short, plain steps. | R195 |
| Models first, drawings last: model-only PRs, then every drawing regenerated in one pass (`regen_pending` in `drawing-models.json` meanwhile). | R196 |

Gates: `cad/check_drawings_current.py` (R183, R196) and `cad/check_drawing_rules.py` (R184 - R196, reads the `<pdf>.checks.json` report the handbuilt-cad engine writes beside every drawing, DRAWING-RULES 24-30), both in `check_all.py`.
