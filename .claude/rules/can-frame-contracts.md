---
paths:
  - bench/**
  - link_g4x_can_setup.json
  - CAN-BUS-ID-ALLOCATION-TABLE.md
  - CANBUS-LINK-G4X-CONFIG.md
---

# CAN Frame Contracts

- Keep frame IDs `0x3E8`-`0x3F1` and `0x640`-`0x643` consistent with `link_g4x_can_setup.json`.
- For any encode/decode change in `bench/frames.py`, update matching docs in `CAN-BUS-ID-ALLOCATION-TABLE.md`.
- Preserve BigEndian packing for multibyte fields unless an existing source explicitly contradicts it.
- Keep warning-bit definitions in sync with `WARN_*` constants in `bench/frames.py`.
- Validate changes using `python bench/can_bench.py ... monitor --known-only` or equivalent targeted checks.
