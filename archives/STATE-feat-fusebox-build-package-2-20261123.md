# STATE (max 30 lines, overwrite only)
Repo: st185-link-ecu-config
Branch: feat/fusebox-build-package-2
Last_Verified_SHA: 0919c93e
Updated: 2026-11-23 -- fuse box CAD worker pass 2 (session_014aA8s2 subagent): items 1-4 done, item 5 not needed (model unchanged)

## Current Goal
- Objective: Fuse box pass 2 (BACKLOG row 107). Worktree .claude/worktrees/fusebox-pass2. Work-hub design ST185_fusebox_rev7 still v1 (no change); no revF.
- Spec_Ref: DECISIONS E3 a, D8 b, "Fuse box model in the work hub"

## Active Blocker
- Status: NONE
- Detail: none

## Next Single Step
- [NEXT] Coordinator: review the PR; Dan picks the model-change route (desktop Fusion on the work account vs Compute) and the sign-ins for the missing hardware models.
- [OPEN] Item 1: Compute = TypeScript only (Python text commands refused, no fs, no local files); geometry edits work on the direct design; one font (Artifakt Element, no Arial) so lid text cannot be re-cut; MCP.IO import works from a public HTTPS STEP URL (Klauke 2R5 test, scratch doc).
- [OPEN] Item 2: spec.LID_TEXT (rev 8 K-FP / SPARE) read by build_fusion etch, commit 0919c93e; applies at the next full build.
- [OPEN] Item 3 CNC: bars, NEG bar, batt bar, pad, LOGIC strips pass; C-strap flags: 4 sharp kerf-root corners (0.5 kerf x 3.0 deep = 6:1), PEM hole C/L-to-edge exactly at PEM minimum (strips 6.90 / 7.10, strap 7.2). Propose only.
- [OPEN] Item 4: Klauke 1R6 / 2R5 / 3R5 / 6R8 filed to models st185_vendor-parts_1101 revA (MANIFEST ok); TE rings already in te\. TBD sign-in: McMaster 94459A140, Accu SSCF-M3-10-A4, PEM x3 (user-info form), RS PRO x13 (RS 403 to the built-in browser). EFC 10S00052/56 publish no CAD. Klauke 3R5MS no 3D.
- [OPEN] Klauke maker STEP 2R5 is 28.5 long; POWER list says l 22 - check the Klauke table. 3R5MS list b 13 / l 26 vs 3R5 model 12 / 31.5.
- [OPEN] PR #716 open. Main _scratch\fb-pass2-show holds Dan's 3 CNC PNGs (delete after Dan has seen them); my work scratch deleted.

## Pointers
- Branch_States: none
- Backlog: BACKLOG.md
- Latest_ADR: "Fuse box model in the work hub" (2026-11-23)
