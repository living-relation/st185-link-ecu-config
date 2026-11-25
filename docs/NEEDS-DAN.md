# Open questions for Dan

## Needs Dan

Open questions for Dan, the ONLY place they live (DECISIONS R119); `docs/needs_dan.py` reads this table. Dispatch keeps it current on every check-in: add a row with the next ID (R115), restate it in full when repeated, delete the row once Dan answers (the answer goes into DECISIONS). Options: `a) label; b) label`, one lower-case letter each (Dan G4 a, 2026-11-25); Recommended: the letter, or several letters when the circumstances differ ("a if ..., else b"; Dan 2026-10-31). Header only = nothing waiting.

| ID | Topic | Question | Options | Recommended |
|---|---|---|---|---|
| G7 | Fuse box screw heads | The rev 8 parts lists use small DIN 933 hex head screws in two kinds of spots: heads trapped in printed hex pockets under the copper (POWER bar studs M5 x 16 / M8 x 25, battery relay block bar studs; the hex stops them turning while the top nut is torqued), and heads on top turned with a tool (AMI ear screws through the copper straps, LOGIC feed screws M4 x 8 / M5 x 10 into the PEM nuts, HCR150 flange screws M6). Which become socket head cap screws? | a) only the turned-from-the-top ones; trapped heads stay hex head screws; b) all of them, with round head pockets plus another anti-turn feature; c) none this rev | a |

This file holds only that table (Dan A96 a, 2026-11-19): `docs/needs_dan.py` reads it for `.github/scripts/test_docs_gates.py` and the fuse box clearance waivers (`cad/fusebox/src/check_clearance.py`). Question IDs: `.claude/rules/questions.md`.
