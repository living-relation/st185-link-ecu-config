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
- One approved exception (2026-09-04): the Gear byte of `0x3EB` (`ST185: Gear`), added solely to drive a
  reverse-camera auto-switch on RealDash. See `CAN-CONFIG-STATUS.md` and the SCOPE note in
  `link_g4x_realdash.xml`. Do not widen this to other `0x3E8–0x3EE` bytes without updating both.
- Maintain conversion parity between XML formulas and `bench/frames.py` scaling.
- Keep warning bits (`startbit`) mapped to canonical byte-6 bit assignments.
- When touching `rd-build/link_g4x_realdash.xml`, confirm parity with root `link_g4x_realdash.xml`.
