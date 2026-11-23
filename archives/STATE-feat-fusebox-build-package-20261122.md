# STATE (max 30 lines, overwrite only)
Repo: st185-link-ecu-config
Branch: feat/fusebox-build-package
Last_Verified_SHA: b0651ff0
Updated: 2026-11-22 -- fuse box CAD worker (session_014aA8s2 subagent): PR #712 open (items 1, 2, 3, 6 done; 4, 5, 7 not started)

## Current Goal
- Objective: Fuse box build package (BACKLOG row 107, Dan 2026-11-14). Worktree .claude/worktrees/fusebox-build-package. Fusion ST185_fusebox_rev7 v60 = models revE; model NOT changed, no revF, no drawing or parts-list change. PR #712 (commit b0651ff0): cad/fusebox/src/wiring_file.py + rev8/fusebox-wiring-{power,logic,battrelay}.pdf and PNG pages, wired renders and wiring_report.json re-run on v60, cad/README.md.
- Spec_Ref: none

## Active Blocker
- Status: NONE
- Detail: none

## Next Single Step
- [NEXT] Coordinator: review PR #712 and the 39 PNGs in main _scratch/fb-build-show (16 wiring pages, 3 lids, 20 wired renders); show Dan; merge when checks are green.
- [OPEN] Wired check on v60: 11 wire / printed-part contacts in LOGIC (pan 8, base 3; 0.03 - 33.7 mm3; w_csb12 33.7, w_hr_86_cp 27.7, w_hl_cp 9.3 base). v58 report had 0 (older than the A82 wire sizes). Fix = wiring_sim.py lane packing; it changes in-box lengths the layout tree mirrors (A35), so it needs Dan / the wiring owner.
- [OPEN] Lid labels: 74 of 74 match sot + spec rev 8. Style only, ask Dan: "K_FP" (code K-FP), "SP" on BUS2-12 (others SPARE), "FAN 2" vs "FAN2 30A". A change = model rebuild, v61, revF, FB-102 / 106 / 109 class drawings.
- [OPEN] Crimp tools TBD in the wiring files: 42281-1, 280919-2, 280756-4, 282110-1, 36161, 320572, 320554, 53941-1, PV10-56R; MCP 2.8 die per wire size (539722-2 / 539723-2). Read TE tooling pages with Claude in Chrome (te.com blocks scripts), then fill TERMINAL in wiring_file.py.
- [OPEN] Not started: item 4 (maker models for hardware and rings, HB fasteners; SR Hardware Library project seen in Fusion), item 5 (wire / splice bodies, one Fusion doc per fabricated part, cnc-part-check on copper), item 7 (revF chain). POWER fuse-lug-to-relay cables have no path in wiring_plan.json (drawn dashed).
- [OPEN] Fusion route used: desktop MCP at http://127.0.0.1:27182/mcp from the PC (the remote Fusion tool timed out at 80 s; Fusion Compute connected later and cannot run the Python viewport render). Fusion title bar: trial ends in 8 days. Scratch _scratch/fbp in the worktree is mine (delete after merge).

## Pointers
- Branch_States: none
- Backlog: BACKLOG.md
- Latest_ADR: D8 b (Dan, 2026-11-22)
