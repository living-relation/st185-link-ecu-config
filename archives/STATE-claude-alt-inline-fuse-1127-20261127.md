# STATE (max 30 lines, overwrite only)
Repo: st185-link-ecu-config
Branch: claude/alt-inline-fuse-1127
Last_Verified_SHA: none
Updated: 2026-11-27 -- chat session_014aA8s4 (H3 a in the master; gates green)

## Current Goal
- Objective: H3 a - the alternator fuse is the sealed inline MEGA holder ALT-FUSE (Littelfuse 880014 + Blue Sea 5104 175 A) beside the jump bar; master first, then every surface that names the old MRBF block.
- Spec_Ref: docs/harness/redesign/DECISIONS.md "H3 a"

## Active Blocker
- Status: NONE
- Detail: none

## Next Single Step
- [NEXT] PR, merge when green; then rebuild the harness.design HeavyDC file from the master (gen_heavydc.py; ALT-FUSE is a new connector part) and post its link.
- [OPEN] H2 (NEEDS-DAN): build_drawings.py prints "solder splice" on splice ends where the master names a lug or solder sleeve.

## Pointers
- Branch_States: generated
- Backlog: BACKLOG.md
- Latest_ADR: H3 a (2026-11-27)
