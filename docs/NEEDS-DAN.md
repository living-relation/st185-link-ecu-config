# Open questions for Dan

## Needs Dan

Open questions for Dan, the ONLY place they live (DECISIONS R119); `docs/needs_dan.py` reads this table. Dispatch keeps it current on every check-in: add a row with the next ID (R115), restate it in full when repeated, delete the row once Dan answers (the answer goes into DECISIONS). Options: `a) label; b) label`, one lower-case letter each (Dan G4 a, 2026-11-25); Recommended: the letter, or several letters when the circumstances differ ("a if ..., else b"; Dan 2026-10-31). Header only = nothing waiting.

| ID | Topic | Question | Options | Recommended |
|---|---|---|---|---|
| G7 | Fuse box screw heads | Which parts-list items become socket head cap screws? Turned from the top with a tool: "RS PRO A2/304 stainless hex bolt M5 x 10, DIN 933" (POWER: AMI ear through each copper strap; LOGIC: feeds into the PEM nuts), "RS PRO A2/304 stainless hex bolt M4 x 8, DIN 933" (LOGIC feeds), "RS PRO stainless (A4 / 316) hex bolt M6 x 16, DIN 933" (BATTRELAY: 2 HCR150 flange). Head trapped in a printed hex pocket under the copper (the hex stops it turning while the top nut is torqued): "RS PRO stainless hex bolt M5 x 16, DIN 933 (grade not stated on the listing)" (POWER and BATTRELAY input studs), "RS PRO stainless hex bolt M8 x 25, DIN 933 (grade not stated on the listing)" (POWER bus studs), "RS PRO stainless hex bolt M5 x 12, DIN 933 (feature text: A4 / 316)" (BATTRELAY output stud), and the M6 x 16 feed stud. | a) only the turned-from-the-top ones; trapped heads stay as they are; b) all of them, with round head pockets plus another anti-turn feature; c) none this rev | a |

This file holds only that table (Dan A96 a, 2026-11-19): `docs/needs_dan.py` reads it for `.github/scripts/test_docs_gates.py` and the fuse box clearance waivers (`cad/fusebox/src/check_clearance.py`). Question IDs: `.claude/rules/questions.md`.
