# Open questions for Dan

## Needs Dan

Open questions for Dan, the ONLY place they live (DECISIONS R119); `docs/needs_dan.py` reads this table. Dispatch keeps it current on every check-in: add a row with the next ID (R115), restate it in full when repeated, delete the row once Dan answers (the answer goes into DECISIONS). Options: `A) label; B) label`; Recommended: the letter, or several letters when the circumstances differ ("A if ..., else B"; Dan 2026-10-31). Header only = nothing waiting.

| ID | Topic | Question | Options | Recommended |
|---|---|---|---|---|
| A98 | Fuse box drawings | How should crimped terminals be shown in the section views (asked in the coordinator chat, 2026-11-19)? | A) answer with the options given in the coordinator chat; B) withdraw the question | A |
| A99 | Fuse box R1 | Which terminal goes on the R1 relay 87a pin (asked in the coordinator chat, 2026-11-19)? | A) answer with the options given in the coordinator chat; B) withdraw the question | A |
| A100 | Fuse box R2 | How should the R2 Mini ISO relay text read (asked in the coordinator chat, 2026-11-19)? | A) answer with the options given in the coordinator chat; B) withdraw the question | A |
| A101 | PR #705 | Do you approve the #705 "what left and where" list so the state-init PR can merge (A90 b)? | A) answer with the options given in the coordinator chat; B) withdraw the question | A |
| A102 | CLAUDE.md | Is it OK that #705 deletes CLAUDE.md, so Claude Code relies on AGENTS.md alone (asked in the coordinator chat, 2026-11-19)? | A) answer with the options given in the coordinator chat; B) withdraw the question | A |
| A103 | Git hooks | What should happen to Cursor's commit-msg / prepare-commit-msg hooks, which no longer run under the workstation hook pack (asked in the coordinator chat, 2026-11-19)? | A) answer with the options given in the coordinator chat; B) withdraw the question | A |

This file holds only that table (Dan A96 a, 2026-11-19): `docs/needs_dan.py` reads it for `.github/scripts/test_docs_gates.py` and the fuse box clearance waivers (`cad/fusebox/src/check_clearance.py`). Question IDs: `.claude/rules/questions.md`.
