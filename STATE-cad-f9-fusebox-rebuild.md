# STATE (max 30 lines, overwrite only)
Repo: st185-link-ecu-config
Branch: cad/f9-fusebox-rebuild
Last_Verified_SHA: a0490839
Updated: 2026-11-25 -- chat session_014aA8s4 (F9 lug sizes done; rebuild next)

## Current Goal
- Objective: G1 fuse box closeout, finalize models: full fuse box rebuild with F9 (lug sizes, SR Fasteners for every fastener), E3 a LID_TEXT, F8 a C-strap w_low 14.2.
- Spec_Ref: docs/harness/redesign/SPEC.md#milestones-and-done-criteria

## Active Blocker
- Status: NONE
- Detail: none

## Next Single Step
- [NEXT] Take the fusion-desktop lock (projects-AGENTS.md section 5), run cad/fusebox/src/build_fusion.py in desktop Fusion (personal account, F1 a temporary; trial ends 12-01) with SR Fasteners placing every fastener incl. PEM.
- [OPEN] SR Fasteners catalog (sr-fastener ec6cc1e) has no EFC compression limiters; EFC publishes no CAD (archive STATE-feat-fusebox-build-package-2): keep the data-sheet limiter bodies (LIMITER_M6 10S00056, 10S00052) unless a maker model turns up.
- [OPEN] After the build: verify close lug fits against the data sheet; copy to work hub (Compute: setActiveHub SparkleBots); AP242 STEP + .f3d to OneDrive models\st185_fusebox_1101 new rev; drawings + BOM from the model (rule 30); CNC check.

## Pointers
- Branch_States: generated
- Backlog: BACKLOG.md
- Latest_ADR: F9 (lug sizes landed in 7ce82bfc)
