---
paths:
  - bench/**
  - rd-build/**
  - link_g4x_can_setup.json
  - link_g4x_can_setup.lcs
  - link_g4x_realdash.xml
  - switchboard_frames.json
  - apps/trackcluster-can-sender/**
  - st185_dash.rd
  - CAN-BUS-ID-ALLOCATION-TABLE.md
  - CAN-BUS-MASTER-DESIGN.md
  - REALDASH-LAYOUT.md
  - ECUMASTER_SWITCHBOARD_SETUP.md
  - BENCH-TEST.md
  - realdash-simulation.html
  - docs/harness/redesign/DECISIONS.md
---
# CAN Frame Contracts - pointer only

- **The rule** (any CAN change on any device reconciles against Link ECU, center cluster,
  RealDash and CSB3; bus facts; authority order with the frozen cluster first):
  `docs/harness/redesign/DECISIONS.md` Rule 2.
- **Who reads which frame** (CSB3 0x640-0x642 -> ECU only; cluster 0x3E8-0x3EB, 0x3EE;
  RealDash 0x3EB gear byte + 0x3EF-0x3F1; cluster sends 0x3EC/0x3ED):
  `docs/harness/redesign/DECISIONS.md` B16.
- **Contract details** (IDs, encode/decode scale forms, BigEndian, `WARN_*` bits, which files
  must agree) and the parity gate `python bench/check_parity.py`:
  `.claude/skills/update-can-frame-contract/SKILL.md`.
- Cluster decode truth: `C:\projects\active\center-cluster-esp32-p4\main\canbus.c`.
- Validate with targeted `bench/can_bench.py` command paths before finalizing.

This file restates nothing, so it cannot drift. A mismatch found and not fixed in the same
pass goes into `docs/OPEN-ITEMS.md`, never left silent.
