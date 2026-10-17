# Drawing rules (st185 shop drawings)

Rules every shop drawing in this repo follows. Decisions are in
`docs/harness/redesign/DECISIONS.md`; rev letters are in `cad/DRAWING-REVS.md`.

| Rule | Source |
|---|---|
| Never show hidden lines in any view. Center marks and center lines for holes and radii are kept (and added where useful). | R150 (Dan 2026-10-17) |
| The model drives the rev letter; drawing and model letters always match. Letters skip I, L, O, Q; Rev A only for a brand-new model. Drawing-only (clerical) changes to a released drawing add .01, .02 ...; a model change bumps the letter. | R147 |
| Redlines go on the drawing first, then the model is fixed, then the drawing is regenerated from the model. | R147 |
| No rev in file names; the letter lives in the title block and the register. | R148 |
| Every model says what made it (`MADE-WITH.md` + register column). | R149 |
| Edges the CAD can't break cleanly are a drawing note, not modelled. | R138 |
