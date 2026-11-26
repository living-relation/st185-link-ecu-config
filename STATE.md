# STATE (max 30 lines, overwrite only)
Repo: st185-link-ecu-config
Branch: main
Last_Verified_SHA: a0490839
Updated: 2026-11-25 -- chat session_014aA8s3 (F9 recorded; handoff for the rebuild chat)

## Current Goal
- Objective: G1 wiring sorted to build. Harness files are complete (Dan 2026-11-21); the fuse box closeout is the live work, in Dan's order: cross-check -> finalize models -> drawings and build material (DECISIONS "Fuse box closeout order").
- Spec_Ref: docs/harness/redesign/SPEC.md#milestones-and-done-criteria

## Active Blocker
- Status: NONE
- Detail: none

## Next Single Step
- [NEXT] Full fuse box rebuild: build_fusion.py in desktop Fusion, personal account for now (F1 a temporary): LID_TEXT (E3 a), SR Fasteners for every fastener incl. PEM/EFC (F2 a); then move to the work hub, export STEP (+ .f3d) to OneDrive, regenerate drawings. C-strap 7.1 edge accepted (F8 a).
- [OPEN] Fuse box working model = work hub SparkleBots > Dan > Personal > ST185 Fuse Box, ST185_fusebox_rev7 v1 (bought-part files go in its Parts folder; build_fusion.open_doc still looks in Default Project: fix in the rewrite) (lineage urn:adsk.wipprod:dm.lineage:eduK3w5PQvmtjVVucnHprQ). Compute (headless): setActiveHub SparkleBots first; small geometry edits only. Before the rebuild (F9): spec.py LUG_6AWG b 13 -> 12 and the parts-list 3R5MS width 12 (Klauke data sheet); SR Fasteners is the clone C:\projects\active\sr-fastener (PEM nuts / studs / standoffs / floating nuts); check it has the EFC spacers, else download maker CAD. SPARE lid label fits (checked 2026-11-24).
- [WAIT] Sanitation sweep 14 only after the other chat is up to speed (Dan B9, 2026-11-20).

## Pointers
- Branch_States: generated
- Backlog: BACKLOG.md; every CAD model: rebuild only with its original method, see repo cad/README.md "Where created" (handbuilt-cad rule 28)
- Latest_ADR: F9; State drift watcher on demand; F8 a; F1 a temporary
- Last_Cleanup: 2026-11-25 @ e7c444c4
- Kept_Branches: none
- Question_Counter: H3