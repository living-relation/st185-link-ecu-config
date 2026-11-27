# Open questions for Dan

## Needs Dan

Open questions for Dan, the ONLY place they live (DECISIONS R119); `docs/needs_dan.py` reads this table. Dispatch keeps it current on every check-in: add a row with the next ID (R115), restate it in full when repeated, delete the row once Dan answers (the answer goes into DECISIONS). Options: `A) label; B) label`; Recommended: the letter, or several letters when the circumstances differ ("A if ..., else B"; Dan 2026-10-31). Header only = nothing waiting.

| ID | Topic | Question | Options | Recommended |
|---|---|---|---|---|
| H2 | Splice-end parts in the wire lists | build_drawings.py writes "solder splice" in a wire list's contact column on every splice end, even where the master names the real part there: the jump-bar lugs 6R10 / 5R10 on SP-JUMP-1 .. -4 and the solder sleeves D-436-37 (SP-GNDOUT-ENG) / D-436-38 (SP-HORN). The master is right; the generated wire lists (and the harness.design files built the same way) drop those parts. | A) fix build_drawings.py to print the master's splice-end part (wire lists regenerate, the harness.design files are rebuilt after); B) leave it | A |

This file holds only that table (Dan A96 a, 2026-11-19): `docs/needs_dan.py` reads it for `.github/scripts/test_docs_gates.py` and the fuse box clearance waivers (`cad/fusebox/src/check_clearance.py`). Question IDs: `.claude/rules/questions.md`.
