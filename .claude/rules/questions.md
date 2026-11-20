---
description: How questions for Dan are numbered, asked and recorded (always on)
---
# Questions for Dan

- Question IDs: one letter + one digit (A1-Z9; Dan 2026-11-01), two characters, asked with the question tool. IDs come round again, so always cite the date with the ID.
- The last used ID is the store STATE `Question_Counter`; the next question takes the next ID. Every answer goes into DECISIONS (search the ID or the date).
- Open questions wait in the `docs/NEEDS-DAN.md` table (A96 a); delete the row once Dan answers.
- Enforcer: `.github/scripts/test_docs_gates.py` (the Needs Dan table parses); the ID format: none yet.
