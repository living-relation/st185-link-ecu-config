# STATE (max 30 lines, overwrite only)
Repo: st185-link-ecu-config
Branch: fusebox-rev8-next
Last_Verified_SHA: 79bd4e63
Updated: 2026-11-21 -- fuse box CAD worker (session_014aA8s2 subagent): v60 built, filed as revE, PR #710 updated

## Current Goal
- Objective: Fuse box model closeout (BACKLOG row 107). Done in the model: Fusion ST185_fusebox_rev7 v60 (C9 a, C1 a, C2 a, C8 a, B4 a, B5 a, T-cutout), models folder st185_fusebox_1101 revE (revD = the v59 step), drawings FB-100P AG / 100L Z / 101 AA / 105 W, PR #710 (commits 7b4249b3, 79bd4e63). D1 a: Fusion only through the Autodesk Fusion MCP. D4 a: this chat alone runs the fuse box closeout. Worktree .claude/worktrees/fusebox-rev8-build.
- Spec_Ref: none

## Active Blocker
- Status: BLOCKED
- Detail: PR #710 fails tools/check_all.py on build_project_bom.py --check only (PROJECT-BOM stale by 3 POWER lines); the sot guard (.claude/sot.json) refuses a BOM commit without a wire list change. Waiting on Dan: do not touch the registry, do not bypass the hook, BOM stays as on main.

## Next Single Step
- [NEXT] Coordinator: review PR #710 and the 33 pictures in main _scratch/fb-closeout-show (7 renders, 9 before / after sections, 17 drawing sheets); show Dan; merge only after the PROJECT-BOM answer.
- [OPEN] All box gates pass on v60: check_terminal_holes (L1 with side play, new X1 top exit, min 0.3), printed_solid, walls, clearance, parts_lists --check, drawings current / rules.
- [OPEN] Least X1 overlap is the micro coil seat (280919-2): 0.45 worst case, 0.60 centred, 3.2 skin. Least catch: MCP 2.8 0.32 centred each side.
- [OPEN] Not re-run: the wired renders in cad/fusebox/rev8 (v58 runs). Models folder holds revA - revE; nothing deleted (Dan's yes needed).
- [OPEN] TBD: TE 63467-1 crimp height. Root STATE Question_Counter is D7 (D5, D7 open with Dan; D2 / D3 belong to Wiring-Main).

## Pointers
- Branch_States: none
- Backlog: BACKLOG.md
- Latest_ADR: T-cutout (Dan, 2026-11-21)
