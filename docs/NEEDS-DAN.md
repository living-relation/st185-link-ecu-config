# Open questions for Dan

## Needs Dan

Open questions for Dan, the ONLY place they live (DECISIONS R119); `docs/needs_dan.py` reads this table. Dispatch keeps it current on every check-in: add a row with the next ID (R115), restate it in full when repeated, delete the row once Dan answers (the answer goes into DECISIONS). Options: `A) label; B) label`; Recommended: the letter, or several letters when the circumstances differ ("A if ..., else B"; Dan 2026-10-31). Header only = nothing waiting.

| ID | Topic | Question | Options | Recommended |
|---|---|---|---|---|
| F2 | PEM and EFC hardware (was E14) | Are the PEM press-in nuts / studs and the EFC spacers in the SR Fasteners add-in, so they are placed with it like every other fastener? | A) yes, place them with SR Fasteners; B) no, add the maker models to the SR library first | A |
| F3 | C-strap kerf roots (was E13) | The CNC check found 4 sharp kerf roots on the copper C-strap. | A) add round reliefs at the kerf roots; B) leave them sharp | A |
| F4 | Maker-model sign-ins (was E12) | PEM, McMaster and Accu need a sign-in or form to download their STEP models. | A) Dan downloads them into the vendor-parts folder; B) use the SR library copies only | A |

This file holds only that table (Dan A96 a, 2026-11-19): `docs/needs_dan.py` reads it for `.github/scripts/test_docs_gates.py` and the fuse box clearance waivers (`cad/fusebox/src/check_clearance.py`). Question IDs: `.claude/rules/questions.md`.
