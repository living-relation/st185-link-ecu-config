# STATE (max 30 lines, overwrite only)
Repo: st185-link-ecu-config
Branch: main
Last_Verified_SHA: a0490839
Updated: 2026-11-23 -- chat session_014aA8s2 (live state moved into the repo, workstation D-2026-11-22)

## Current Goal
- Objective: G1 wiring sorted to build. Harness files are complete (Dan 2026-11-21); the fuse box closeout is the live work, in Dan's order: cross-check -> finalize models -> drawings and build material (DECISIONS "Fuse box closeout order").
- Spec_Ref: docs/harness/redesign/SPEC.md#milestones-and-done-criteria

## Active Blocker
- Status: NONE
- Detail: none

## Next Single Step
- [NEXT] Full fuse box rebuild: build_fusion.py in desktop Fusion, personal account for now (F1 a temporary; trial ends 12-01): LID_TEXT (E3 a), SR Fasteners for every fastener incl. PEM/EFC (F2 a); then move to the work hub, export STEP (+ .f3d) to OneDrive, regenerate drawings. C-strap 7.1 edge accepted (F8 a).
- [OPEN] Fuse box working model = work hub SparkleBots > Dan > Personal > Default Project, ST185_fusebox_rev7 v1 (lineage urn:adsk.wipprod:dm.lineage:eduK3w5PQvmtjVVucnHprQ). Compute: setActiveHub SparkleBots first; small geometry edits only. Parts-list sizes to check against Klauke's table: 2R5 l 22 vs STEP 28.5; 3R5MS b13 / l26 vs 3R5 model 12 / 31.5. Not checked: SPARE fits the mini fuse label space.
- [WAIT] Sanitation sweep 14 only after the other chat is up to speed (Dan B9, 2026-11-20).

## Pointers
- Branch_States: generated
- Backlog: BACKLOG.md; every CAD model: rebuild only with its original method, see repo cad/README.md "Where created" (handbuilt-cad rule 28)
- Latest_ADR: F8 a; F1 a temporary
- Last_Cleanup: 2026-11-15 @ 3420c3c4
- Kept_Branches: none
- Question_Counter: F8