# STATE-fusebox-twistlock-clips (branch merged: [DONE] PR #704, b83efd3e, 2026-11-19)

Archived 2026-11-19 by state-init (Dan A92 a): verbatim copy of the fusebox-retention handoff (snapshot C:\projects\active\st185-link-ecu-config\_scratch\state-init-retention-handoff-snapshot.md). Read-only history; live state is STATE.md, open work is BACKLOG.md.

# Handoff: fuse box terminal retention (A76 - A86) - finish drawings, revC, PR
_Written 2026-11-17 05:55 ET by the wiring-main coordinator (Claude Code cloud session 014aA8s38hXaVB1xcx7s768g). Previous agent stopped at the weekly usage limit (resets 2026-11-20 21:00 ET)._

## Start
1. Read `AGENTS.md`, DECISIONS "Fuse box rev 8" (A62 - A86), "Drawing rules" (model first, R197 tightened, A81 / A83 / A84), and this file. Project rule: ALL CAD work follows the handbuilt-cad repo rules (`C:\projects\active\handbuilt-cad`, its AGENTS / CLAUDE / drawing docs): models first, drawings generated from the model only, drawing rev letter = model rev letter, never edit a drawing or assembly drawing by hand, parts lists / BOM generated from the model.
2. Work only in the worktree below. Desktop Commander for PC work and git. Fusion lock (workstation `agents/projects-AGENTS.md` s.5) before driving Fusion; Dan's AutodeskFusionMCP add-in (Autodesk's built-in MCP server must be off).

## State (verified 2026-11-17)
- Worktree `.claude\worktrees\twistlock-clips`, branch `fusebox/twistlock-clips`, head `b6f99a19` (main #702 merged in), clean, 5 commits ahead of origin/main, NOT pushed, no PR.
- Fusion `ST185_fusebox_rev7` **v58**, saved and exported to the worktree `cad/fusebox/rev8`. Fusion lock free.
- Commit `7862fea2` (v58): R1 30/87 on TE 63467-1 lance seats (A86 a, 30 A / 10 AWG), R1 clip and FB-104 retired, HEAD_EST replaced by TE drawing values, spec.CRIMP from TE docs, parts lists + PROJECT-BOM regenerated. Model checks green: terminal holes, clearance, printed solid, walls 0, strap / strip sweeps.
- Twist-lock code kept but unused (TWIST_KINDS empty): only R1 ever had the extra clip; every other press-in seat passed (A79 / A80 withdrawn).

## Left to do (in order)
1. Confirm the handbuilt-cad drawing rules and rev-letter scheme (drawing letter must match the model letter). If `cad/drawings/run_fb_rev8.py` conflicts with handbuilt-cad, STOP and report to the coordinator.
2. Regenerate every drawing `cad/check_drawings_current.py` lists (expected FB-100P, 100L, 100B, 101, 102, 103, 106, 109; FB-104 retired) from the v58 export, with REVLOG rows and rev marks. Windows `handbuilt-cad\.venv` python (the WSL path in the docstring is stale).
3. File models + drawings + parts lists into OneDrive `models\st185_fusebox_1101\revC` with publish-to-models; verify MANIFEST.
4. Gates: `tools/check_all.py` (HARD tracer gate), `check_wiring.py`, `build_drawings.py --check`, `check_corridors.py`, `bench/check_parity.py`, `.github/scripts/test_docs_gates.py`, `tune/scripts/validate_tune.py`, `cad/check_drawings_current.py`, `parts_lists --check`.
5. Run pr-closeout (OPEN-ITEMS row 107 + History + Current state date), push, open PR "fix: fuse box terminal retention to official specs; R1 spare 30 A / 10 AWG (A76-A86)", body `Rows: 107` and the Claude Code footer; merge on green CI.
6. Clean up: remove the worktree and branch, `_scratch\twistlock` (delete by name, including its handbuilt-cad clone); then delete this handoff.

## Remaining TBDs (official number not found)
- TE 2293255-1 head height (no seat uses it).
- TXL minimum insulation OD (M22759/16 minimum used).
- 14 AWG GXL exceeds the MCP insulation grip (1-968851-1, 1.9 - 3.0): wiring note in the LOGIC parts list (A83), no box / master change.

## Do not
- Change the master, sot/* (except text notes Dan approved), layout or harness.design files (A48 a).
- Estimate any size (A81). Ask about part picks or model downloads (A84, part rule).
- Force-push or rebase.
