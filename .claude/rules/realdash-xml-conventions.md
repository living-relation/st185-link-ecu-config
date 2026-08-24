---
paths:
  - link_g4x_realdash.xml
  - REALDASH-LAYOUT.md
  - realdash-simulation.html
  - rd-build/link_g4x_realdash.xml
---

# RealDash XML Conventions

- Keep `ST185:` input names stable; renames break existing `.rd` gauge bindings.
- Restrict RealDash frame scope to documented ECU streams (`0x3EF`, `0x3F0`, `0x3F1`) unless architecture docs change.
- Maintain conversion parity between XML formulas and `bench/frames.py` scaling.
- Keep warning bits (`startbit`) mapped to canonical byte-6 bit assignments.
- When touching `rd-build/link_g4x_realdash.xml`, confirm parity with root `link_g4x_realdash.xml`.
