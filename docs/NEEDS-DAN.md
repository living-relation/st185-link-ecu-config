# Open questions for Dan

## Needs Dan

Open questions for Dan, the ONLY place they live (DECISIONS R119); `docs/needs_dan.py` reads this table. Dispatch keeps it current on every check-in: add a row with the next ID (R115), restate it in full when repeated, delete the row once Dan answers (the answer goes into DECISIONS). Options: `A) label; B) label`; Recommended: the letter, or several letters when the circumstances differ ("A if ..., else B"; Dan 2026-10-31). Header only = nothing waiting.

| ID | Topic | Question | Options | Recommended |
|---|---|---|---|---|
| G1 | Fuse box: SR Fasteners | How do SR Fasteners parts go into the fuse box build (F2 a, F9)? build_fusion.py draws all 16 fastener kinds itself today. | A) two stages: rebuild now, then a second script swaps every fastener for an SR Fasteners part; B) one stage: rewrite the fastener code to call SR Fasteners, then one rebuild; C) keep hand-drawn fasteners this rev, SR Fasteners next rev | A |
| G2 | Repo cleanup leftovers | Which cleanup leftovers should be done (pick any)? | A) draft automation.yml for review; B) move the two old _research TASK cards to the store _archive; C) drop the stale 2026-11-22 work-hub sentence from the store INDEX | A |
| G3 | Bought-part files | How do assemblies use the bought-part files (DECISIONS "Bought parts are their own files")? | A) linked: Fusion points at the part file, edits flow to every assembly; B) imported copy: simpler, edits do not flow | A |

This file holds only that table (Dan A96 a, 2026-11-19): `docs/needs_dan.py` reads it for `.github/scripts/test_docs_gates.py` and the fuse box clearance waivers (`cad/fusebox/src/check_clearance.py`). Question IDs: `.claude/rules/questions.md`.
