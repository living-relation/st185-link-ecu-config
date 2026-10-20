# CAN Frame Contracts - pointer only

- **The rule** (any CAN change on any device reconciles against Link ECU, center cluster,
  RealDash and CSB3; bus facts; authority order with the frozen cluster first):
  `docs/RECONCILIATION-RULES.md` Rule 2.
- **Who reads which frame** (CSB3 0x640-0x642 -> ECU only; cluster 0x3E8-0x3EB, 0x3EE;
  RealDash 0x3EB gear byte + 0x3EF-0x3F1; cluster sends 0x3EC/0x3ED):
  `docs/harness/redesign/DECISIONS.md` B16.
- **Contract details** (IDs, encode/decode scale forms, BigEndian, `WARN_*` bits, which files
  must agree) and the parity gate `python bench/check_parity.py`: `AGENTS.md` "Working Rules".
- Cluster decode truth: `C:\projects\active\center-cluster-esp32-p4\main\canbus.c`.

This file restates nothing, so it cannot drift. A mismatch found and not fixed in the same
pass goes into `docs/OPEN-ITEMS.md`, never left silent.
