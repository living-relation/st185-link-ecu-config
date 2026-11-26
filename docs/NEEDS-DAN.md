# Open questions for Dan

## Needs Dan

Open questions for Dan, the ONLY place they live (DECISIONS R119); `docs/needs_dan.py` reads this table. Dispatch keeps it current on every check-in: add a row with the next ID (R115), restate it in full when repeated, delete the row once Dan answers (the answer goes into DECISIONS). Options: `a) label; b) label`, one lower-case letter each (Dan G4 a, 2026-11-25); Recommended: the letter, or several letters when the circumstances differ ("a if ..., else b"; Dan 2026-10-31). Header only = nothing waiting.

| ID | Topic | Question | Options | Recommended |
|---|---|---|---|---|
| H2 | Lock washer under the AMI ear screws | Is this the BelMetric washer meant: Nord-Lock wedge-lock washer pair (cam faces inside, radial teeth outside that bite into the screw head and the copper), stainless, for the M5 ear screws? Sizes: NL5ss-254 (ID 5.4, OD 9.0, T 2.2 mm) or NL5spss-254 enlarged (OD 10.8). Not in SR Fasteners (its catalog leaves out wedge-lock washers), so it comes from Nord-Lock's own CAD (H1 b). | a) yes, NL5ss-254 (OD 9.0 sits under the 8 mm hex head); b) yes, NL5spss-254 enlarged; c) a different washer (describe or link it) | a |
| G8 | Fuse box parts lists from the model BOM | The rebuild sets part number, description and material on every component, then the fuse box parts lists come from the model's BOM. Dan usually needs only the BOM, and most fuse box items are parts he makes; the screws are easy to buy from their BOM lines. What happens to the vendor / link / price / spares columns now typed by hand in cad/fusebox/src/parts_lists.py? | a) the parts lists are the model BOM only (part number, description, material, qty); the hand-typed buying columns go, and buying help is given only when Dan asks for a part; b) model BOM plus the hand-typed buying columns kept beside it, matched by part number | a |
This file holds only that table (Dan A96 a, 2026-11-19): `docs/needs_dan.py` reads it for `.github/scripts/test_docs_gates.py` and the fuse box clearance waivers (`cad/fusebox/src/check_clearance.py`). Question IDs: `.claude/rules/questions.md`.
