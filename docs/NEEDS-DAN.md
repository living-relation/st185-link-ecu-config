# Open questions for Dan

## Needs Dan

Open questions for Dan, the ONLY place they live (DECISIONS R119); `docs/needs_dan.py` reads this table. Dispatch keeps it current on every check-in: add a row with the next ID (R115), restate it in full when repeated, delete the row once Dan answers (the answer goes into DECISIONS). Options: `A) label; B) label`; Recommended: the letter, or several letters when the circumstances differ ("A if ..., else B"; Dan 2026-10-31). Header only = nothing waiting.

| ID | Topic | Question | Options | Recommended |
|---|---|---|---|---|
| B4 | Fuse box drawings | Show crimped terminals in the fuse box section views? | A) yes, model the crimp from TE's official crimp sizes; B) no, TE's uncrimped maker models are enough | A |
| B5 | Fuse box R1 | R1 87a has a 42281-1 terminal modelled, but A16 a says only the cavity stays cut: what now? | A) remove the terminal and keep the cut cavity; B) keep it | A |
| B6 | Fuse box R2 | sot/fuse-relay-map.csv calls R2 (K-EFI) "Mini ISO", but the part is the F7 1-1414147-0: fix the text? | A) fix the text to F7; B) leave it | A |
| B1 | PR #705 | Approve the #705 "what left and where" list and merge? | A) yes, merge; B) Dan reads the list first | A |
| B2 | CLAUDE.md | CLAUDE.md was deleted by the fold: bring it back? | A) keep a one-line CLAUDE.md containing only "@AGENTS.md"; B) leave it deleted | A |
| B3 | Git hooks | The hook pack drops Cursor's commit-msg / prepare-commit-msg hooks: what now? | A) chain them back in; B) leave them off | A |

This file holds only that table (Dan A96 a, 2026-11-19): `docs/needs_dan.py` reads it for `.github/scripts/test_docs_gates.py` and the fuse box clearance waivers (`cad/fusebox/src/check_clearance.py`). Question IDs: `.claude/rules/questions.md`.
