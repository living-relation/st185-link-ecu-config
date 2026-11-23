---
description: How questions for Dan are numbered, asked and recorded (always on)
---
# Questions for Dan

- Question IDs: two characters only, one letter + one digit: A1-A9, B1-B9 ... Z9, then wrap to A1 (Dan 2026-11-01; standing rule restated 2026-11-20, DECISIONS "Question IDs (Dan, 2026-11-20)"). Asked with the question tool. An ID only has to be unique while its question is open; DECISIONS always records the ID with its date.
- The last used ID is the `STATE.md` `Question_Counter`; the next question takes the next ID. Every answer goes into DECISIONS (search the ID or the date).
- Open questions wait in the `docs/NEEDS-DAN.md` table (A96 a); delete the row once Dan answers.
- Enforcer: `.github/scripts/test_docs_gates.py` (the Needs Dan table parses, and every open ID is `[A-Z][1-9]`).
