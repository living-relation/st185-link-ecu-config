# STATE (max 30 lines, overwrite only)
Repo: st185-link-ecu-config
Branch: docs/models-hub-rule
Last_Verified_SHA: none
Updated: 2026-11-22 -- worker of chat session_014aA8s2 (Fusion personal hub -> models folder / work hub)

## Current Goal
- Objective: Dan 2026-11-22: copy the ST185 Fusion documents out of his personal hub (trial ending) to the models folder and into SparkleBots "Dan/Personal"; record the rule (DECISIONS "Models home and Fusion hub").
- Spec_Ref: docs/harness/redesign/DECISIONS.md "Models home and Fusion hub (Dan, 2026-11-22)"

## Active Blocker
- Status: BLOCKED
- Detail: work-hub upload only. No route into the work hub without Dan: desktop Fusion sees only hub "dgrip"; Fusion Compute cannot read PC files (MCP.IO import = STEP / IGES / SAT by URL only); Chrome and the built-in browser are not signed in to the work Autodesk account.

## Next Single Step
- Done: Inventories: `_scratch/fusion-migration/inventory-personal.json` (154 files, 7 projects) and `inventory-work-personal.json` (45 files, all v1, uploaded 2026-11-21).
- Done: 28 ST185 / fasteners documents: latest version -> `<models job>\fusion-archive-2026-11-22\` (.f3d + root .step, README, ARCHIVE-INDEX.json with counts, MANIFEST.sha256). 27 archives re-imported in desktop Fusion with identical counts and volume. revE `ST185_fusebox_rev8.f3d` re-imports as v60 (74 components, 816 bodies).
- [OPEN] `Default Project/VRC Enclosure/ST185-VRC-Enclosure` v5 (external reference to the Cnlinko connector): STEP only; needs File > Export .f3z in the Fusion window. An export with the link broken crashed Fusion twice on re-import: do not retry that.
- [NEXT] After Dan picks the upload route: upload each archive to "Dan/Personal/<project>/<folder>" keeping the document name (skip anything already there), then verify in Fusion Compute (counts vs ARCHIVE-INDEX.json, one STEP export), then record the new URNs in DECISIONS and `cad/README.md`.
- [OPEN] Not archived (Dan to decide): the other 82 documents missing from the work hub (custom-pdm 54, Admin Project 21, Default Project 6, Templates 1).

## Pointers
- Branch_States: none
- Backlog: BACKLOG.md
- PR: #713 (open, not merged)
- Latest_ADR: Models home and Fusion hub (Dan, 2026-11-22)
