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
- [NEXT] G1 b rewrite of build_fusion.py (rev 8 path): drop the hand-made fastener bodies, record each fastener's hole, then place it with SR Fasteners (fastener_place.place_stack, via desktop Fusion MCP under the fusion-desktop lock). Map (A2 = finish SS): Ear/Bar/Lug/Flange bolts ISO 4017 (DIN 933) -> HHB-M; Nut_DIN934 + Nut_M5_M6 -> NHX-M; LugNut DIN 6923 + "Keps" M5/M8 (parts list = DIN 6923) -> NSF-M; Washer DIN 127B M4 -> WSL-M; Nut_PEM S-M4/M5 -> press-in S; Stud_PEM FHS-M5 -> press-in FHS. Not in SR: EFC limiters -> own linked part file (G3 a). Clearance / report checks that read fastener bodies by name must read the SR occurrences. Rev 6-only standoff + set screw untouched.
- [OPEN] Bought parts as own files (DECISIONS 2026-11-25): EFC limiters 10S00056 / 10S00052 sizes verified vs EFC table 2026-11-25; save each as its own part file in st185_vendor-parts_1101\efc\ (index cad/vendor/INDEX.md) and use it from there, same for every other bought part built in-script. Waiting on G1 (SR Fasteners approach), G2 (cleanup), G3 (linked vs imported part files): docs/NEEDS-DAN.md.
- [OPEN] After the build: verify close lug fits against the data sheet; copy to work hub (Compute: setActiveHub SparkleBots); AP242 STEP + .f3d to OneDrive models\st185_fusebox_1101 new rev; drawings + BOM from the model (rule 30); CNC check.

## Pointers
- Branch_States: generated
- Backlog: BACKLOG.md
- Latest_ADR: Bought parts are their own files (2026-11-25); F9 lug sizes landed in 7ce82bfc
