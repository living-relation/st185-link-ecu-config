---
paths:
  - link_g4x_realdash.xml
  - REALDASH-LAYOUT.md
  - realdash-simulation.html
---

# RealDash XML Conventions - pointer only

The RealDash XML rules (stable `ST185:` names, frame scope 0x3EF-0x3F1 plus the 0x3EB gear
byte exception, conversion parity with `bench/frames.py`, byte-6 warning bits, the root XML
is the single copy) are owned by `AGENTS.md` "Working Rules", checked by
`python bench/check_parity.py`. Frame routing: `docs/harness/redesign/DECISIONS.md` B16.
