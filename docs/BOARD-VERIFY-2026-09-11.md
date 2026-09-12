# ST185 project board verify - 2026-09-11

## Purpose
Capture **board claim vs live git** conflicts so ACTIVE work crowns on `shipping\st185-link-ecu-config` instead of husk-keyed chat memory.

Not a living progress board. Not auto-updating. Paste **CONFLICT rows only** into the ACTIVE trance; park the rest.

## Sources
- Board artifact (stale snapshot, last updated **2026-09-01**, overall **71%**): https://claude.ai/public/artifacts/db1cbe48-09ad-4415-b968-43803d01d95b
- Live repo: `C:\projects\shipping\st185-link-ecu-config` (HEAD `1dbb4b5` at verify time)
- Verify author: Grimoire (Grim Council 2026-09-11)
- Scoring lamps (Gizmo): **Git** / **Board claim** / **Session memory** (husk-keyed Claude/Cursor). Conflict = any two disagree.

## Year lock (Daniel 2026-09-11)
- Locked: **1993** (repo docs). Board's **1991** was wrong — do not use 1991.
## CONFLICT rows (ink these into ACTIVE)

| Item | Git | Board | Session* | Conflict |
|------|-----|-------|----------|----------|
| Cluster / RealDash / CAN ~70% | Contracts + `.rd` exist; bench unchecked; RealDash **not** CAN-validated | "Core system working" | Husk piles may still say "done / working" | **Git != Board** (+ likely session) |
| Wiring ~95% | Band 3 **unwired**; pins unverified vs Link PDF; ignition colours C11 open | "Every channel assigned" @95% | May treat schematic as SoT | **Git != Board** |
| CAN infra ~60% | Topology settled (5-node, 1 Mbit); **C18 termination open** | "Termination settled" | May echo "settled" | **Git != Board** |
| ECU / tune ~50% | Base map **not designed**; `tune/` seeds only | "Tune maps not reviewed" | May think pin side closed | **Git != Board** (wording) |
| Year | Docs **1993** | was **1991** | — | **RESOLVED → 1993** |
| Paths | Live under `shipping\` | Board silent | ~28 Claude keys still `C--projects-st185-...` | **Session != Git** |

\*Session = husk-keyed trance memory - not readable from disk; flag is structural.

## Park (non-conflicts / inconclusive)
- RealDash layout automation skill - **verified** in sibling `shipping\realdash-dashboard-builder` (parked after import).
- Sensors and components as **device/pin inventory** - mostly OK as design claim; physical location not proven in-repo.
- Engine build % / rear LSD % - **inconclusive** from git (garage state); identity claims coherent if garage matches.
- Board math (~71%) checks; content is ~10 days stale vs post-Sep 1 merges (harness PRs #17/#18, IC/turbo, Turbo Speed rd-build, Gear/reverse-cam carve-out, ECU handoff, open **PR #19**).

## Ground-truth unfinished (at verify)
- PR **#19** open (Cloud env / CAN-virtual notes)
- ECU first-start / base map
- Bench pass + RealDash live CAN validation
- Physical pin verify + Band 3 loom + termination ends
- Docs cleanup / handoff corrections still pending (including old path citations)

## Intra-corpus poison (not on board; agents still trip)
- RealDash "still being built" in `CAN-CONFIG-STATUS` vs `.rd` "build is done"
- Cabin temp still listed in `BENCH-TEST.md` (handoff `1dbb4b5` flags it, **not applied**)
- Free-byte note still claims `0x3E9` bytes 5-7 free while fuel pressure owns 5-6
- Docs still cite old `C:\projects\st185-...` / root cluster paths instead of `shipping\`

## HOLD
This verify does **not** clear the car-stack HOLD. Crown ACTIVE on `shipping\` paths, park husk chats, then Wick sweeps. See `C:\projects\docs\project-structure.md`.

## How to use
1. Open `shipping\st185-link-ecu-config` once; crown one ACTIVE session.
2. Paste only the CONFLICT table above into that session.
3. Do not reopen the ~28 husk-keyed Claude sessions to re-argue green checkmarks.
